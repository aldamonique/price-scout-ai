from pydantic import BaseModel

from price_scout.domain.catalog.models import Category


class ProductGroup(BaseModel):
    name: str
    category: Category
    width_cm: float | None
    depth_cm: float | None
    height_cm: float | None
    offer_ids: list[str]


class DiscardedOffer(BaseModel):
    offer_id: str
    reason: str


class Judgment(BaseModel):
    products: list[ProductGroup]
    discarded: list[DiscardedOffer]
