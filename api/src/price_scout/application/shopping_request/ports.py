from collections.abc import Callable
from typing import Protocol

from price_scout.application.shopping_request.tool_models import (
    CategoryMetricsInput,
    CategoryMetricsResult,
    CheckFitInput,
    CheckFitResult,
    PlanBudgetInput,
    PlanBudgetResult,
    SearchOffersInput,
    SearchOffersResult,
)
from price_scout.domain.shopping_request.models import AgentPlan, AgentUsage, ShoppingRequest


class AgentTools(Protocol):
    def plan_budget(self, request: PlanBudgetInput) -> PlanBudgetResult: ...

    def search_offers(self, request: SearchOffersInput) -> SearchOffersResult: ...

    def check_fit(self, request: CheckFitInput) -> CheckFitResult: ...

    def category_metrics(self, request: CategoryMetricsInput) -> CategoryMetricsResult: ...


class ShoppingAgent(Protocol):
    def run(self, request: ShoppingRequest, tools: AgentTools) -> tuple[AgentPlan, AgentUsage]: ...


class JobRunner(Protocol):
    def submit(self, job: Callable[[], None]) -> None: ...
