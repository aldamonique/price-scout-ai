from typing import Literal

from pydantic import BaseModel, Field

from price_scout.domain.catalog.models import Category
from price_scout.domain.shopping_request.models import BudgetLine


class ToolResult(BaseModel):
    summary: str
    stage_ms: dict[str, int] | None = Field(default=None, exclude=True)


class PlanBudgetInput(BaseModel):
    lines: list[BudgetLine] = Field(
        description="How much goes to each item, in the market's currency. Without a budget, "
        "an estimate of what each item usually costs."
    )


class PlanBudgetResult(ToolResult):
    leftover: float | None


class SearchOffersInput(BaseModel):
    query: str = Field(
        description="What to search for, in the market's language, as a shopper would type it."
    )
    category: Category = Field(description="The product category.")
    max_price: float | None = Field(description="Maximum price in the market's currency, or null.")
    max_width_cm: float | None = Field(description="Maximum width in centimeters, or null.")
    prefer_words: list[str] = Field(
        description=(
            "Words from the user's preferences (color, flavor, material, brand) in English, as"
            ' they appear in a product name, e.g. ["red"] or ["vanilla"]. Products whose name has'
            " them are listed first. Empty when the user has no preference for this item."
        )
    )


class ProductSummary(BaseModel):
    id: str
    name: str
    width_cm: float | None
    min_price: float
    store_count: int
    max_installments: int | None
    matches_preferences: bool


class SearchOffersResult(ToolResult):
    products: list[ProductSummary]


class CheckFitInput(BaseModel):
    product_id: str = Field(description="The product id, exactly as search_offers returned it.")
    max_width_cm: float = Field(description="The available width, in centimeters.")


class CheckFitResult(ToolResult):
    verdict: Literal["fits", "does_not_fit", "unknown"]


class CategoryMetricsInput(BaseModel):
    category: Category = Field(description="The furniture category.")


class CategoryMetricsResult(ToolResult):
    product_count: int
    avg_price: float | None
    min_price: float | None
    max_price: float | None
