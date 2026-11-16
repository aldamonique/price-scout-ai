import pytest

from price_scout.infrastructure.llm.usage import ModelPricing, UsageMeter

AGENT = ModelPricing(input_usd_per_mtok=2, output_usd_per_mtok=10)
JUDGE = ModelPricing(input_usd_per_mtok=1, output_usd_per_mtok=5)


def test_each_call_is_priced_with_its_own_model() -> None:
    meter = UsageMeter()

    meter.add(1_000_000, 100_000, AGENT)
    meter.add(1_000_000, 100_000, JUDGE)

    usage = meter.usage()
    assert (usage.input_tokens, usage.output_tokens) == (2_000_000, 200_000)
    assert usage.cost_usd == pytest.approx(4.5)


def test_one_unpriced_call_makes_the_total_unknown() -> None:
    meter = UsageMeter()

    meter.add(1000, 100, AGENT)
    meter.add(1000, 100, None)
    meter.add(1000, 100, JUDGE)

    assert meter.usage().cost_usd is None
