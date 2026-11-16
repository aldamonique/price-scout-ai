from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from price_scout.domain.catalog.models import Market, Product

StepKind = Literal["plan", "replan", "search", "measure", "metrics"]
RequestStatus = Literal["queued", "running", "done", "failed"]


class Preferences(BaseModel):
    brands: str | None = Field(default=None, max_length=200)
    colors: str | None = Field(default=None, max_length=200)
    materials: str | None = Field(default=None, max_length=200)
    payment: str | None = Field(
        default=None, max_length=200, description='e.g. "up to 10 installments"'
    )
    notes: str | None = Field(default=None, max_length=400)

    def as_lines(self) -> list[str]:
        labels = {
            "brands": "Preferred brands",
            "colors": "Colors",
            "materials": "Materials",
            "payment": "Payment",
            "notes": "Other requirements",
        }
        return [
            f"{label}: {value}"
            for field, label in labels.items()
            if (value := getattr(self, field))
        ]


class AgentStep(BaseModel):
    number: int
    kind: StepKind
    tool: str
    summary: str
    duration_ms: int
    ok: bool
    stage_ms: dict[str, int] | None = None


class BudgetLine(BaseModel):
    item: str
    amount: float


class PlanChoice(BaseModel):
    item: str
    product_id: str
    reason: str
    max_width_cm: float | None
    differences: str | None


class AgentPlan(BaseModel):
    choices: list[PlanChoice]
    unmet: list[str]


class AgentUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = None
    agent_model: str | None = None
    agent_prompt_version: str | None = None


class SearchStats(BaseModel):
    searches: int = 0
    listings: int = 0
    discarded: int = 0


class PlanItem(BaseModel):
    item: str
    product: Product
    reason: str
    differences: str | None = None
    max_width_cm: float | None = None
    fits: bool | None = None
    savings: float


class ShoppingPlan(BaseModel):
    market: Market
    budget: float | None
    total: float
    leftover: float | None
    items: list[PlanItem]
    unmet: list[str]
    insights: list[str]
    stats: SearchStats
    usage: AgentUsage


class ShoppingRequest(BaseModel):
    id: str
    description: str
    market: Market
    budget: float | None
    preferences: Preferences
    status: RequestStatus
    steps: list[AgentStep] = []
    plan: ShoppingPlan | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class RequestSummary(BaseModel):
    id: str
    description: str
    market: Market
    budget: float | None
    status: RequestStatus
    total: float | None
    item_count: int
    created_at: datetime
