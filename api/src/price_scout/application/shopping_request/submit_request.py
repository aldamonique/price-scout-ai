import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from price_scout.application.shopping_request.ports import JobRunner
from price_scout.application.shopping_request.run_request import RunShoppingRequest
from price_scout.domain.catalog.models import Market
from price_scout.domain.errors import RateLimitedError
from price_scout.domain.shopping_request.models import Preferences, ShoppingRequest
from price_scout.domain.shopping_request.ports import ShoppingRequestRepository


class SubmitShoppingRequest:
    def __init__(
        self,
        requests: ShoppingRequestRepository,
        runner: JobRunner,
        run_request: RunShoppingRequest,
        max_per_hour: int | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._requests = requests
        self._runner = runner
        self._run_request = run_request
        self._max_per_hour = max_per_hour
        self._now = now

    def execute(
        self, description: str, market: Market, budget: float | None, preferences: Preferences
    ) -> ShoppingRequest:
        now = self._now()
        if self._max_per_hour is not None:
            recent = self._requests.count_since(now - timedelta(hours=1))
            if recent >= self._max_per_hour:
                raise RateLimitedError(self._max_per_hour)
        request = ShoppingRequest(
            id=uuid.uuid4().hex,
            description=description,
            market=market,
            budget=budget,
            preferences=preferences,
            status="queued",
            created_at=now,
            updated_at=now,
        )
        self._requests.save(request)
        self._runner.submit(lambda: self._run_request.execute(request.id))
        return request
