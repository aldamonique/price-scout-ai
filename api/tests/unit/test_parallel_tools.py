import threading
from typing import Any, cast

from openai.types.responses import ParsedResponseFunctionToolCall

from price_scout.application.shopping_request.tool_models import (
    CategoryMetricsInput,
    CategoryMetricsResult,
    CheckFitInput,
    CheckFitResult,
    PlanBudgetInput,
    PlanBudgetResult,
    SearchOffersInput,
    SearchOffersResult,
)
from price_scout.infrastructure.llm.agent_tools import OpenAiAgentTools


class BlockingTools:
    def __init__(self, parties: int) -> None:
        self._barrier = threading.Barrier(parties, timeout=5)

    def plan_budget(self, request: PlanBudgetInput) -> PlanBudgetResult:
        return PlanBudgetResult(summary="", leftover=None)

    def search_offers(self, request: SearchOffersInput) -> SearchOffersResult:
        self._barrier.wait()
        return SearchOffersResult(summary=request.query, products=[], stage_ms={"fetch": 1})

    def check_fit(self, request: CheckFitInput) -> CheckFitResult:
        raise NotImplementedError

    def category_metrics(self, request: CategoryMetricsInput) -> CategoryMetricsResult:
        raise NotImplementedError


def search_call(call_id: str, query: str) -> ParsedResponseFunctionToolCall:
    arguments: dict[str, Any] = {
        "query": query,
        "category": "books",
        "max_price": None,
        "max_width_cm": None,
        "prefer_words": [],
    }
    return ParsedResponseFunctionToolCall(
        type="function_call",
        call_id=call_id,
        name="search_offers",
        arguments="{}",
        parsed_arguments=arguments,
    )


def test_searches_asked_in_the_same_turn_run_at_the_same_time() -> None:
    tools = OpenAiAgentTools(BlockingTools(parties=3))
    calls = [search_call(f"c{n}", f"book {n}") for n in range(3)]

    replies = cast(list[dict[str, Any]], tools.answer(calls))

    assert [reply["call_id"] for reply in replies] == ["c0", "c1", "c2"]
    assert all("error" not in str(reply["output"]) for reply in replies)


def test_the_stage_timings_are_not_sent_back_to_the_model() -> None:
    tools = OpenAiAgentTools(BlockingTools(parties=1))

    reply = cast(list[dict[str, Any]], tools.answer([search_call("c1", "book")]))[0]

    assert "stage_ms" not in str(reply["output"])
