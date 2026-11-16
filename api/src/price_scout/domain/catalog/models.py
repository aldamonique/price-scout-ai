from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Category = Literal[
    "furniture",
    "electronics",
    "appliances",
    "books",
    "food",
    "health",
    "beauty",
    "fashion",
    "home",
    "sports",
    "toys",
    "pets",
    "auto",
    "other",
]


class Market(BaseModel):
    country: str = Field(pattern=r"^[a-z]{2}$", description='Google country code, e.g. "br".')
    language: str = Field(pattern=r"^[a-z]{2}(-[a-z]{2})?$", description='e.g. "pt-br", "en".')
    currency: str = Field(pattern=r"^[A-Z]{3}$", description='ISO 4217 code, e.g. "BRL".')


class SearchIntent(BaseModel):
    query: str
    category: Category
    market: Market
    max_price: float | None = None
    max_width_cm: float | None = None


class RawSearch(BaseModel):
    search_id: str
    query: str
    country: str
    fetched_at: datetime
    payload: dict[str, Any]


class Offer(BaseModel):
    offer_id: str
    title: str
    store: str
    price: float
    url: str | None = None
    image_url: str | None = None


class StoreOffer(BaseModel):
    store: str
    price: float
    url: str | None = None
    store_icon: str | None = None
    installment_months: int | None = None
    installment_amount: float | None = None


class Product(BaseModel):
    id: str
    name: str
    category: Category
    width_cm: float | None = None
    dimensions: str | None = None
    image_url: str | None = None
    min_price: float
    store_count: int
    offers: list[StoreOffer]


class SearchResult(BaseModel):
    search_id: str
    offer_count: int
    discarded_count: int
    products: list[Product]
    stage_ms: dict[str, int] = {}


class CategoryStats(BaseModel):
    category: Category
    country: str
    product_count: int
    avg_price: float | None
    min_price: float | None
    max_price: float | None
