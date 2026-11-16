from price_scout.domain.errors import RequestNotFoundError
from price_scout.domain.shopping_request.models import ShoppingRequest
from price_scout.domain.shopping_request.ports import ShoppingRequestRepository


class GetShoppingRequest:
    def __init__(self, requests: ShoppingRequestRepository) -> None:
        self._requests = requests

    def execute(self, request_id: str) -> ShoppingRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise RequestNotFoundError(request_id)
        return request
