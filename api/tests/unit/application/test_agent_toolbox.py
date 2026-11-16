import threading

import pytest
from builders import product, shopping_request
from fakes import ScriptedAgent, new_toolbox

from price_scout.application.shopping_request.step_log import StepLog
from price_scout.application.shopping_request.tool_models import (
    CategoryMetricsInput,
    CheckFitInput,
    PlanBudgetInput,
    SearchOffersInput,
)
from price_scout.application.shopping_request.toolbox import AgentToolbox, _summary
from price_scout.domain.shopping_request.models import AgentStep, BudgetLine


def budget(amount: float) -> PlanBudgetInput:
    return PlanBudgetInput(lines=[BudgetLine(item="Sofa", amount=amount)])


SEARCH = SearchOffersInput(
    query="sofá", category="furniture", max_price=None, max_width_cm=None, prefer_words=[]
)


def test_each_tool_call_becomes_a_step() -> None:
    toolbox = new_toolbox()

    ScriptedAgent().run(shopping_request(), toolbox)

    steps = toolbox.step_log.steps
    assert [step.kind for step in steps] == ["plan", "search", "measure"]
    assert steps[0].summary == "1 item: Sofa R$ 2,800.00"
    assert steps[1].summary == '"sofá 3 lugares": 2 listings, 1 discarded, 1 product'


def test_searches_use_the_request_market_and_count_what_was_seen() -> None:
    toolbox = new_toolbox()

    toolbox.search_offers(SEARCH)
    toolbox.search_offers(SEARCH)

    assert (toolbox.stats.searches, toolbox.stats.listings, toolbox.stats.discarded) == (2, 4, 2)


def test_the_split_cannot_exceed_the_request_budget() -> None:
    toolbox = new_toolbox(request=shopping_request(budget=1000))

    with pytest.raises(ValueError, match="over the budget"):
        toolbox.plan_budget(budget(1200))

    assert toolbox.step_log.steps[0].ok is False


def test_the_step_log_reports_every_new_step() -> None:
    seen: list[list[AgentStep]] = []
    toolbox = new_toolbox(StepLog(on_change=seen.append))

    toolbox.plan_budget(budget(2800))

    assert [len(steps) for steps in seen] == [1]


def test_a_second_budget_plan_is_a_replan() -> None:
    toolbox = new_toolbox()

    toolbox.plan_budget(budget(2800))
    toolbox.plan_budget(budget(2900))

    assert [step.kind for step in toolbox.step_log.steps] == ["plan", "replan"]


def test_category_metrics_are_read_for_the_request_market() -> None:
    result = new_toolbox().category_metrics(CategoryMetricsInput(category="furniture"))

    assert (result.avg_price, result.summary) == (1180, "average furniture price: R$ 1,180.00")


def test_checking_a_product_no_search_returned_is_an_error() -> None:
    with pytest.raises(ValueError, match="was not returned"):
        new_toolbox().check_fit(CheckFitInput(product_id="made-up", max_width_cm=200))


def test_the_agent_sees_the_most_installments_any_store_offers() -> None:
    assert _summary(product(installments=10), []).max_installments == 10
    assert _summary(product(), []).max_installments is None


def test_the_toolbox_is_typed_against_the_agent_tools_interface() -> None:
    assert isinstance(new_toolbox(), AgentToolbox)


def test_without_a_budget_any_split_is_accepted() -> None:
    toolbox = new_toolbox(request=shopping_request(budget=None))

    result = toolbox.plan_budget(budget(99_999))

    assert result.leftover is None
    assert toolbox.step_log.steps[0].ok is True


def test_steps_added_from_many_threads_get_unique_numbers() -> None:
    log = StepLog()

    threads = [
        threading.Thread(target=log.add, args=("search", "search_offers", "ok", 0.0, True))
        for _ in range(20)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(step.number for step in log.steps) == list(range(1, 21))


def test_search_steps_keep_the_stage_timings() -> None:
    toolbox = new_toolbox()

    toolbox.search_offers(SEARCH)

    assert set(toolbox.step_log.steps[0].stage_ms or {}) == {"fetch", "silver", "judge", "gold"}


def test_search_results_flag_the_products_that_match_the_preferences() -> None:
    toolbox = new_toolbox()

    sofa = toolbox.search_offers(SEARCH.model_copy(update={"prefer_words": ["sofa"]}))
    other = toolbox.search_offers(SEARCH.model_copy(update={"prefer_words": ["red"]}))

    assert [p.matches_preferences for p in sofa.products] == [True]
    assert [p.matches_preferences for p in other.products] == [False]
