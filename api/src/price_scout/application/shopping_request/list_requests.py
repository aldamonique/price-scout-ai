from price_scout.domain.shopping_request.models import RequestSummary
from price_scout.domain.shopping_request.ports import ShoppingRequestRepository


class ListShoppingRequests:
    MAX_LIMIT = 200

    def __init__(self, requests: ShoppingRequestRepository) -> None:
        self._requests = requests

    def execute(self, limit: int = 50) -> list[RequestSummary]:
        return self._requests.recent(min(max(limit, 1), self.MAX_LIMIT))
