from price_scout.domain.errors import RequestNotFoundError
from price_scout.domain.observability.models import LlmCall
from price_scout.domain.observability.ports import CallLog
from price_scout.domain.shopping_request.ports import ShoppingRequestRepository


class GetRequestCalls:
    def __init__(self, requests: ShoppingRequestRepository, calls: CallLog) -> None:
        self._requests = requests
        self._calls = calls

    def execute(self, request_id: str) -> list[LlmCall]:
        if self._requests.get(request_id) is None:
            raise RequestNotFoundError(request_id)
        return self._calls.calls(request_id)
