from typing import Protocol

from price_scout.domain.catalog.models import (
    Category,
    CategoryStats,
    Offer,
    Product,
    RawSearch,
    SearchIntent,
)


class OfferSource(Protocol):
    def fetch(self, intent: SearchIntent) -> RawSearch: ...


class RawStore(Protocol):
    def save(self, raw: RawSearch) -> None: ...

    def load(self, search_id: str) -> RawSearch | None: ...


class Catalog(Protocol):
    def offers(self, search_id: str) -> list[Offer]: ...

    def products(self, search_id: str, intent: SearchIntent) -> list[Product]: ...

    def category_stats(self, category: Category, country: str) -> CategoryStats: ...
