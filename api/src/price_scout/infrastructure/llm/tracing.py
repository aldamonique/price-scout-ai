import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel

from price_scout.domain.observability.models import LlmCall, LlmTask
from price_scout.domain.observability.ports import CallLog
from price_scout.infrastructure.llm.structured import LlmResult, StructuredLlm
from price_scout.infrastructure.llm.usage import ModelPricing, UsageMeter

logger = logging.getLogger(__name__)

MAX_ERROR_LENGTH = 300


@dataclass(frozen=True)
class RunContext:
    request_id: str | None
    meter: UsageMeter


_current_run: ContextVar[RunContext | None] = ContextVar("current_run", default=None)


@contextmanager
def tracing(request_id: str | None, meter: UsageMeter) -> Iterator[UsageMeter]:
    token = _current_run.set(RunContext(request_id, meter))
    try:
        yield meter
    finally:
        _current_run.reset(token)


class CallHandle:
    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0

    def tokens(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class NullCallLog:
    def record(self, call: LlmCall) -> None:
        pass

    def calls(self, request_id: str) -> list[LlmCall]:
        return []

    def delete_for_request(self, request_id: str) -> None:
        pass


class CallTracer:
    def __init__(
        self,
        log: CallLog,
        clock: Callable[[], float] = time.perf_counter,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        new_id: Callable[[], str] = lambda: uuid4().hex,
    ) -> None:
        self._log = log
        self._clock = clock
        self._now = now
        self._new_id = new_id

    @contextmanager
    def call(
        self, task: LlmTask, model: str, prompt_version: str, pricing: ModelPricing | None
    ) -> Iterator[CallHandle]:
        handle = CallHandle()
        started = self._clock()
        error: str | None = None
        try:
            yield handle
        except Exception as exc:
            error = (str(exc) or type(exc).__name__)[:MAX_ERROR_LENGTH]
            raise
        finally:
            latency_ms = round((self._clock() - started) * 1000)
            self._record(task, model, prompt_version, pricing, handle, latency_ms, error)

    def _record(
        self,
        task: LlmTask,
        model: str,
        prompt_version: str,
        pricing: ModelPricing | None,
        handle: CallHandle,
        latency_ms: int,
        error: str | None,
    ) -> None:
        run = _current_run.get()
        if run is not None:
            run.meter.add(handle.input_tokens, handle.output_tokens, pricing)
        cost = pricing.cost_usd(handle.input_tokens, handle.output_tokens) if pricing else None
        call = LlmCall(
            id=self._new_id(),
            request_id=run.request_id if run else None,
            task=task,
            model=model,
            prompt_version=prompt_version,
            input_tokens=handle.input_tokens,
            output_tokens=handle.output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            ok=error is None,
            error=error,
            created_at=self._now(),
        )
        try:
            self._log.record(call)
        except Exception:
            logger.warning("could not record the %s call", task, exc_info=True)


class ObservedLlm:
    def __init__(
        self,
        inner: StructuredLlm,
        tracer: CallTracer,
        task: LlmTask,
        model: str,
        prompt_version: str,
        pricing: ModelPricing | None,
    ) -> None:
        self._inner = inner
        self._tracer = tracer
        self._task: LlmTask = task
        self._model = model
        self._prompt_version = prompt_version
        self._pricing = pricing

    def parse[T: BaseModel](
        self, *, task: str, system: str, user: str, output_type: type[T]
    ) -> LlmResult[T]:
        with self._tracer.call(
            self._task, self._model, self._prompt_version, self._pricing
        ) as call:
            result = self._inner.parse(task=task, system=system, user=user, output_type=output_type)
            call.tokens(result.input_tokens, result.output_tokens)
            return result
