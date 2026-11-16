import pytest
from builders import BRAZIL, product

from price_scout.domain.catalog.markets import MARKETS, market_for
from price_scout.domain.shopping_request.models import (
    AgentPlan,
    AgentUsage,
    PlanChoice,
    PlanItem,
    Preferences,
    SearchStats,
)
from price_scout.domain.shopping_request.rules import build_plan, fits, savings, summarize

STATS = SearchStats(searches=1, listings=40, discarded=3)


def choice(product_id: str, differences: str | None = None) -> PlanChoice:
    return PlanChoice(
        item="Sofa",
        product_id=product_id,
        reason="Fits.",
        max_width_cm=210,
        differences=differences,
    )


def test_fits_compares_width_with_the_limit() -> None:
    assert fits(product(width_cm=205), 210) is True
    assert fits(product(width_cm=215), 210) is False


def test_fits_is_unknown_without_width_or_limit() -> None:
    assert fits(product(width_cm=None), 210) is None
    assert fits(product(width_cm=205), None) is None


def test_savings_is_the_gap_between_the_most_and_least_expensive_store() -> None:
    assert savings(product(prices=(1299, 1349, 1529))) == 230


def test_savings_is_zero_with_a_single_store() -> None:
    assert savings(product(prices=(1299,))) == 0


def test_build_plan_computes_totals_from_real_products() -> None:
    agent_plan = AgentPlan(choices=[choice("abc-p1")], unmet=[])

    plan = build_plan(agent_plan, {"abc-p1": product()}, BRAZIL, 3000, STATS, AgentUsage())

    assert (plan.total, plan.leftover) == (1299, 1701)
    assert plan.items[0].fits is True
    assert plan.items[0].savings == 50
    assert (plan.market, plan.budget, plan.stats) == (BRAZIL, 3000, STATS)


def test_build_plan_keeps_what_a_close_match_changes() -> None:
    agent_plan = AgentPlan(choices=[choice("abc-p1", "Gray instead of beige")], unmet=[])

    plan = build_plan(agent_plan, {"abc-p1": product()}, BRAZIL, 3000, STATS, AgentUsage())

    assert plan.items[0].differences == "Gray instead of beige"


def test_build_plan_drops_products_the_agent_made_up() -> None:
    agent_plan = AgentPlan(choices=[choice("made-up")], unmet=[])

    plan = build_plan(agent_plan, {"abc-p1": product()}, BRAZIL, 3000, STATS, AgentUsage())

    assert plan.items == []
    assert plan.unmet == ["Sofa"]


def test_summary_reports_leftover_savings_and_fit() -> None:
    item = PlanItem(
        item="Sofa", product=product(), reason="", max_width_cm=210, fits=True, savings=50
    )

    assert summarize([item], budget=3000, total=1299, currency="BRL") == [
        "The plan is R$ 1,701.00 under budget.",
        "Comparing stores saves up to R$ 50.00.",
        "1 of 1 item with a size limit fit.",
    ]


def test_summary_warns_about_missing_measurements_only_with_a_size_limit() -> None:
    item = PlanItem(
        item="Table", product=product(width_cm=None), reason="", max_width_cm=120, savings=0
    )
    book = PlanItem(item="Book", product=product(width_cm=None), reason="", savings=0)

    assert summarize([item, book], budget=1000, total=1299, currency="EUR") == [
        "The plan is € 299.00 over budget.",
        "No measurements in the listing: Table. Check first.",
    ]


def test_preferences_list_only_what_the_user_filled_in() -> None:
    preferences = Preferences(colors="gray", payment="up to 10 installments")

    assert preferences.as_lines() == ["Colors: gray", "Payment: up to 10 installments"]


def test_every_market_is_found_by_its_country_code() -> None:
    assert market_for("BR") == BRAZIL
    assert all(market_for(code) == market for code, market in MARKETS.items())


def test_an_uncovered_country_has_no_market() -> None:
    with pytest.raises(KeyError):
        market_for("zz")


def test_without_a_budget_the_plan_has_no_leftover() -> None:
    agent_plan = AgentPlan(choices=[choice("abc-p1")], unmet=[])

    plan = build_plan(agent_plan, {"abc-p1": product()}, BRAZIL, None, STATS, AgentUsage())

    assert (plan.budget, plan.leftover, plan.total) == (None, None, 1299)
    assert plan.insights[0] == "No budget was set; the plan totals R$ 1,299.00."
