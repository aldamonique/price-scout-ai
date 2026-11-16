import functools

from price_scout.application.shopping_request.ports import JobRunner
from price_scout.application.shopping_request.run_request import RunShoppingRequest
from price_scout.domain.shopping_request.ports import ShoppingRequestRepository


class ResumeShoppingRequests:
    def __init__(
        self,
        requests: ShoppingRequestRepository,
        runner: JobRunner,
        run_request: RunShoppingRequest,
    ) -> None:
        self._requests = requests
        self._runner = runner
        self._run_request = run_request

    def execute(self) -> int:
        request_ids = self._requests.requeue_unfinished()
        for request_id in request_ids:
            self._runner.submit(functools.partial(self._run_request.execute, request_id))
        return len(request_ids)
