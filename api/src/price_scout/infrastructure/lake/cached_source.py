from collections.abc import Callable
from datetime import UTC, date, datetime

from price_scout.domain.catalog.models import RawSearch, SearchIntent
from price_scout.domain.catalog.ports import OfferSource, RawStore
from price_scout.domain.catalog.rules import search_id_for


class CachedOfferSource:
    def __init__(
        self,
        inner: OfferSource,
        store: RawStore,
        today: Callable[[], date] = lambda: datetime.now(UTC).date(),
    ) -> None:
        self._inner = inner
        self._store = store
        self._today = today

    def fetch(self, intent: SearchIntent) -> RawSearch:
        cached = self._store.load(search_id_for(intent.query, intent.market.country, self._today()))
        if cached is not None:
            return cached
        return self._inner.fetch(intent)
