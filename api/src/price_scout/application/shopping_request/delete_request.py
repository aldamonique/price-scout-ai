from price_scout.domain.errors import RequestInProgressError, RequestNotFoundError
from price_scout.domain.observability.ports import CallLog
from price_scout.domain.shopping_request.ports import ShoppingRequestRepository


class DeleteShoppingRequest:
    def __init__(self, requests: ShoppingRequestRepository, calls: CallLog) -> None:
        self._requests = requests
        self._calls = calls

    def execute(self, request_id: str) -> None:
        request = self._requests.get(request_id)
        if request is None:
            raise RequestNotFoundError(request_id)
        if request.status in ("queued", "running"):
            raise RequestInProgressError(request_id)
        self._calls.delete_for_request(request_id)
        self._requests.delete(request_id)
