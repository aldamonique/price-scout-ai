import functools
import threading
import time
from collections.abc import Callable

from price_scout.application.shopping_request.tool_models import ToolResult
from price_scout.domain.shopping_request.models import AgentStep, StepKind

type StepListener = Callable[[list[AgentStep]], None]


class StepLog:
    def __init__(self, on_change: StepListener | None = None) -> None:
        self.steps: list[AgentStep] = []
        self._on_change = on_change
        self._lock = threading.Lock()

    def has(self, kind: StepKind) -> bool:
        return any(step.kind == kind for step in self.steps)

    def add(
        self,
        kind: StepKind,
        tool: str,
        summary: str,
        started: float,
        ok: bool,
        stage_ms: dict[str, int] | None = None,
    ) -> None:
        duration_ms = round((time.perf_counter() - started) * 1000)
        with self._lock:
            if kind == "plan" and self.has("plan"):
                kind = "replan"
            self.steps.append(
                AgentStep(
                    number=len(self.steps) + 1,
                    kind=kind,
                    tool=tool,
                    summary=summary,
                    duration_ms=duration_ms,
                    ok=ok,
                    stage_ms=stage_ms,
                )
            )
            if self._on_change is not None:
                self._on_change(list(self.steps))


class HasStepLog:
    step_log: StepLog


def recorded[R: ToolResult](
    kind: StepKind,
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    def decorate(tool: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(tool)
        def wrapper(self: HasStepLog, *args: object, **kwargs: object) -> R:
            started = time.perf_counter()
            try:
                result = tool(self, *args, **kwargs)
            except Exception as error:
                self.step_log.add(kind, tool.__name__, f"error: {error}", started, ok=False)
                raise
            self.step_log.add(
                kind, tool.__name__, result.summary, started, ok=True, stage_ms=result.stage_ms
            )
            return result

        return wrapper

    return decorate
