from datetime import UTC, datetime

from price_scout.domain.catalog.models import Market, Product, StoreOffer
from price_scout.domain.shopping_request.models import Preferences, ShoppingRequest

BRAZIL = Market(country="br", language="pt-br", currency="BRL")


def product(
    product_id: str = "abc-p1",
    width_cm: float | None = 205,
    prices: tuple[float, ...] = (1299, 1349),
    installments: int | None = None,
) -> Product:
    return Product(
        id=product_id,
        name="3-Seat Sofa",
        category="furniture",
        width_cm=width_cm,
        min_price=min(prices),
        store_count=len(prices),
        offers=[
            StoreOffer(store=f"Store {i}", price=price, installment_months=installments)
            for i, price in enumerate(prices)
        ],
    )


def shopping_request(
    request_id: str = "r1",
    description: str = "furnish the living room",
    budget: float | None = 3000,
    preferences: Preferences | None = None,
) -> ShoppingRequest:
    now = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    return ShoppingRequest(
        id=request_id,
        description=description,
        market=BRAZIL,
        budget=budget,
        preferences=preferences or Preferences(),
        status="queued",
        created_at=now,
        updated_at=now,
    )
