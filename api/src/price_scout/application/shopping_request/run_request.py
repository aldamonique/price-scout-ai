import logging
from collections.abc import Callable
from datetime import UTC, datetime

from price_scout.application.shopping_request.ports import ShoppingAgent
from price_scout.application.shopping_request.step_log import StepLog
from price_scout.application.shopping_request.toolbox import AgentToolbox
from price_scout.domain.errors import RequestNotFoundError, UpstreamError
from price_scout.domain.shopping_request.models import AgentStep, ShoppingRequest
from price_scout.domain.shopping_request.ports import ShoppingRequestRepository
from price_scout.domain.shopping_request.rules import build_plan

logger = logging.getLogger(__name__)

type ToolboxFactory = Callable[[StepLog, ShoppingRequest], AgentToolbox]


class RunShoppingRequest:
    def __init__(
        self,
        agent: ShoppingAgent,
        new_toolbox: ToolboxFactory,
        requests: ShoppingRequestRepository,
    ) -> None:
        self._agent = agent
        self._new_toolbox = new_toolbox
        self._requests = requests

    def execute(self, request_id: str) -> None:
        stored = self._requests.get(request_id)
        if stored is None:
            raise RequestNotFoundError(request_id)
        current = self._update(stored, status="running")

        def save_progress(steps: list[AgentStep]) -> None:
            nonlocal current
            current = self._update(current, steps=steps)

        toolbox = self._new_toolbox(StepLog(on_change=save_progress), current)
        try:
            agent_plan, usage = self._agent.run(current, toolbox)
            plan = build_plan(
                agent_plan,
                toolbox.products,
                current.market,
                current.budget,
                toolbox.stats,
                usage,
            )
        except UpstreamError as error:
            self._update(current, status="failed", error=str(error))
        except Exception:
            logger.exception("shopping request %s failed", request_id)
            self._update(current, status="failed", error="Unexpected error. Please try again.")
        else:
            self._update(current, status="done", plan=plan)

    def _update(self, request: ShoppingRequest, **changes: object) -> ShoppingRequest:
        updated = request.model_copy(update={**changes, "updated_at": datetime.now(UTC)})
        self._requests.save(updated)
        return updated
