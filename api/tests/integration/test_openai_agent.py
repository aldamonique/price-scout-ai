import pytest
from builders import BRAZIL, shopping_request
from fake_openai import FakeResponsesApi, failing_client, message, tool_call
from fakes import InMemoryCallLog, new_toolbox

from price_scout.domain.catalog.models import Offer, SearchIntent
from price_scout.domain.errors import UpstreamError
from price_scout.domain.shopping_request.models import Preferences
from price_scout.infrastructure.llm.offer_judge import LlmOfferJudge
from price_scout.infrastructure.llm.shopping_agent import OpenAiShoppingAgent
from price_scout.infrastructure.llm.structured import OpenAiStructuredLlm
from price_scout.infrastructure.llm.tracing import CallTracer, ObservedLlm, tracing
from price_scout.infrastructure.llm.usage import ModelPricing, UsageMeter

PLAN = {
    "choices": [
        {
            "item": "Sofa",
            "product_id": "abc-p1",
            "reason": "It fits.",
            "max_width_cm": 210,
            "differences": None,
        }
    ],
    "unmet": [],
}
SCRIPT = [
    [
        tool_call(
            "plan_budget",
            {"lines": [{"item": "Sofa", "amount": 2800}]},
            "c1",
        )
    ],
    [
        tool_call(
            "search_offers",
            {
                "query": "sofá 3 lugares",
                "category": "furniture",
                "max_price": 2800,
                "max_width_cm": 210,
                "prefer_words": [],
            },
            "c2",
        )
    ],
    [message(PLAN)],
]


def agent(api: FakeResponsesApi, max_turns: int = 20) -> OpenAiShoppingAgent:
    return OpenAiShoppingAgent(
        api.client(),
        "test-model",
        {"effort": "medium"},
        "glossary",
        ModelPricing(input_usd_per_mtok=1.0, output_usd_per_mtok=10.0),
        prompt_version="v3",
        max_turns=max_turns,
    )


def test_the_agent_calls_tools_until_it_returns_a_plan() -> None:
    api = FakeResponsesApi(SCRIPT)
    toolbox = new_toolbox()

    plan, usage = agent(api).run(shopping_request(), toolbox)

    assert plan.choices[0].product_id == "abc-p1"
    assert [step.kind for step in toolbox.step_log.steps] == ["plan", "search"]
    assert (usage.input_tokens, usage.output_tokens) == (3000, 600)
    assert usage.cost_usd == pytest.approx(0.009)
    assert (usage.agent_model, usage.agent_prompt_version) == ("test-model", "v3")


def test_every_prompt_version_on_disk_loads() -> None:
    for version in ("v3", "v4"):
        api = FakeResponsesApi([[message(PLAN)]])
        agent = OpenAiShoppingAgent(
            api.client(), "m", None, "glossary", None, prompt_version=version
        )

        _, usage = agent.run(shopping_request(), new_toolbox())

        assert usage.agent_prompt_version == version


def test_the_first_message_carries_the_fixed_facts() -> None:
    api = FakeResponsesApi([[message(PLAN)]])
    request = shopping_request(preferences=Preferences(brands="Tok&Stok"))

    agent(api).run(request, new_toolbox(request=request))

    first = str(api.requests[0]["input"])
    assert "Country: br" in first
    assert "Preferred brands: Tok&Stok" in first


def test_each_turn_sends_only_the_tool_results_and_the_previous_response_id() -> None:
    api = FakeResponsesApi(SCRIPT)

    agent(api).run(shopping_request(), new_toolbox())

    second = api.requests[1]
    assert second["previous_response_id"] == "resp_1"
    assert [item["type"] for item in second["input"]] == ["function_call_output"]
    assert {tool["name"] for tool in api.requests[0]["tools"]} == {
        "plan_budget",
        "search_offers",
        "check_fit",
        "category_metrics",
    }


def test_a_failing_tool_is_reported_back_to_the_model() -> None:
    api = FakeResponsesApi(
        [
            [tool_call("check_fit", {"product_id": "made-up", "max_width_cm": 200}, "c1")],
            [message(PLAN)],
        ]
    )

    agent(api).run(shopping_request(), new_toolbox())

    reply = api.requests[1]["input"][0]["output"]
    assert reply.startswith("error: product made-up was not returned")


def test_the_agent_gives_up_after_the_turn_limit() -> None:
    api = FakeResponsesApi([SCRIPT[0]] * 3)

    with pytest.raises(UpstreamError, match="within 2 turns"):
        agent(api, max_turns=2).run(shopping_request(), new_toolbox())


def test_an_api_error_becomes_an_upstream_error() -> None:
    broken = OpenAiShoppingAgent(
        failing_client(), "test-model", None, "glossary", None, prompt_version="v3"
    )

    with pytest.raises(UpstreamError, match="AuthenticationError"):
        broken.run(shopping_request(), new_toolbox())


def test_the_judge_returns_the_parsed_verdict() -> None:
    verdict = {
        "products": [
            {
                "name": "3-Seat Sofa",
                "category": "furniture",
                "width_cm": 205,
                "depth_cm": None,
                "height_cm": None,
                "offer_ids": ["o1"],
            }
        ],
        "discarded": [{"offer_id": "o2", "reason": "cover"}],
    }
    api = FakeResponsesApi([[message(verdict)]])
    judge = LlmOfferJudge(OpenAiStructuredLlm(api.client(), "test-model", None), "glossary")
    offers = [
        Offer(offer_id="o1", title="Sofá 3 Lugares", store="A", price=1299),
        Offer(offer_id="o2", title="Capa", store="B", price=99),
    ]

    judgment = judge.judge(SearchIntent(query="sofá", category="furniture", market=BRAZIL), offers)

    assert [d.offer_id for d in judgment.discarded] == ["o2"]
    assert "<business_context>" in api.requests[0]["instructions"]


def test_an_incomplete_judge_answer_is_an_error() -> None:
    api = FakeResponsesApi([[]], status="incomplete")
    llm = OpenAiStructuredLlm(api.client(), "test-model", None)
    offers = [Offer(offer_id="o1", title="Sofá", store="A", price=1299)]

    with pytest.raises(UpstreamError, match="incomplete"):
        LlmOfferJudge(llm, None).judge(
            SearchIntent(query="sofá", category="furniture", market=BRAZIL), offers
        )


def test_every_agent_turn_is_recorded_for_the_request() -> None:
    log = InMemoryCallLog()
    traced = OpenAiShoppingAgent(
        FakeResponsesApi(SCRIPT).client(),
        "test-model",
        None,
        "glossary",
        None,
        prompt_version="v3",
        tracer=CallTracer(log),
    )

    traced.run(shopping_request("r9"), new_toolbox())

    assert [(c.request_id, c.task, c.ok) for c in log.recorded] == [("r9", "agent", True)] * 3
    assert {(c.model, c.prompt_version, c.cost_usd) for c in log.recorded} == {
        ("test-model", "v3", None)
    }


def test_judge_calls_are_recorded_as_judge() -> None:
    log = InMemoryCallLog()
    verdict: dict[str, list[object]] = {"products": [], "discarded": []}
    llm = ObservedLlm(
        OpenAiStructuredLlm(FakeResponsesApi([[message(verdict)]]).client(), "judge-model", None),
        CallTracer(log),
        task="judge",
        model="judge-model",
        prompt_version="v1",
        pricing=None,
    )
    offers = [Offer(offer_id="o1", title="Sofá", store="A", price=1299)]

    with tracing("r1", UsageMeter()):
        LlmOfferJudge(llm, None).judge(
            SearchIntent(query="sofá", category="furniture", market=BRAZIL), offers
        )

    assert [(c.request_id, c.task, c.prompt_version) for c in log.recorded] == [
        ("r1", "judge", "v1")
    ]


def test_without_a_budget_the_agent_is_told_so() -> None:
    api = FakeResponsesApi([[message(PLAN)]])
    request = shopping_request(budget=None)

    agent(api).run(request, new_toolbox(request=request))

    assert "Budget: not set (prices in BRL)" in str(api.requests[0]["input"])
