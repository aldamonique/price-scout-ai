from datetime import UTC, datetime

import pytest
from fakes import InMemoryCallLog

from price_scout.domain.observability.models import LlmCall
from price_scout.infrastructure.llm.tracing import CallTracer, tracing
from price_scout.infrastructure.llm.usage import ModelPricing, UsageMeter

PRICING = ModelPricing(input_usd_per_mtok=2, output_usd_per_mtok=10)
NOW = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


class Clock:
    def __init__(self, *readings: float) -> None:
        self._readings = iter(readings)

    def __call__(self) -> float:
        return next(self._readings)


def tracer(log: InMemoryCallLog, *readings: float) -> CallTracer:
    return CallTracer(log, clock=Clock(*readings), now=lambda: NOW, new_id=lambda: "c1")


def test_a_call_is_recorded_with_its_request_tokens_cost_and_latency() -> None:
    log = InMemoryCallLog()
    meter = UsageMeter()

    with tracing("r1", meter), tracer(log, 10.0, 10.25).call("agent", "m", "v3", PRICING) as call:
        call.tokens(1000, 100)

    assert log.recorded == [
        LlmCall(
            id="c1",
            request_id="r1",
            task="agent",
            model="m",
            prompt_version="v3",
            input_tokens=1000,
            output_tokens=100,
            cost_usd=0.003,
            latency_ms=250,
            ok=True,
            error=None,
            created_at=NOW,
        )
    ]
    assert (meter.input_tokens, meter.output_tokens) == (1000, 100)


def test_a_failed_call_is_recorded_and_the_error_still_raised() -> None:
    log = InMemoryCallLog()

    with pytest.raises(TimeoutError), tracer(log, 0.0, 1.0).call("judge", "m", "v1", None):
        raise TimeoutError("model timed out")

    failed = log.recorded[0]
    assert (failed.ok, failed.error, failed.latency_ms) == (False, "model timed out", 1000)
    assert failed.cost_usd is None


def test_calls_outside_a_request_have_no_request_id() -> None:
    log = InMemoryCallLog()

    with tracer(log, 0.0, 0.1).call("judge", "m", "v1", PRICING):
        pass

    assert log.recorded[0].request_id is None


def test_a_broken_call_log_never_breaks_the_request() -> None:
    class BrokenLog(InMemoryCallLog):
        def record(self, call: LlmCall) -> None:
            raise OSError("disk full")

    with tracer(BrokenLog(), 0.0, 0.1).call("agent", "m", "v3", PRICING) as call:
        call.tokens(10, 1)
