import threading

from price_scout.application.search.search_offers import SearchOffers
from price_scout.application.shopping_request.step_log import HasStepLog, StepLog, recorded
from price_scout.application.shopping_request.tool_models import (
    CategoryMetricsInput,
    CategoryMetricsResult,
    CheckFitInput,
    CheckFitResult,
    PlanBudgetInput,
    PlanBudgetResult,
    ProductSummary,
    SearchOffersInput,
    SearchOffersResult,
)
from price_scout.domain.catalog.models import Market, Product, SearchIntent
from price_scout.domain.catalog.ports import Catalog
from price_scout.domain.catalog.rules import preference_matches, rank_by_preference
from price_scout.domain.formatting import money, plural
from price_scout.domain.shopping_request.models import SearchStats

PRODUCTS_PER_SEARCH = 12


class AgentToolbox(HasStepLog):
    def __init__(
        self,
        search_offers: SearchOffers,
        catalog: Catalog,
        step_log: StepLog,
        market: Market,
        budget: float | None,
    ) -> None:
        self._search_offers = search_offers
        self._catalog = catalog
        self.step_log = step_log
        self.market = market
        self.budget = budget
        self.products: dict[str, Product] = {}
        self.stats = SearchStats()
        self._lock = threading.Lock()

    @recorded("plan")
    def plan_budget(self, request: PlanBudgetInput) -> PlanBudgetResult:
        parts = ", ".join(f"{line.item} {self._money(line.amount)}" for line in request.lines)
        summary = f"{plural(len(request.lines), 'item')}: {parts}"
        if self.budget is None:
            return PlanBudgetResult(summary=summary, leftover=None)
        leftover = self.budget - sum(line.amount for line in request.lines)
        if leftover < 0:
            raise ValueError(f"the split is {self._money(-leftover)} over the budget")
        return PlanBudgetResult(summary=summary, leftover=round(leftover, 2))

    @recorded("search")
    def search_offers(self, request: SearchOffersInput) -> SearchOffersResult:
        result = self._search_offers.execute(
            SearchIntent(
                query=request.query,
                category=request.category,
                market=self.market,
                max_price=request.max_price,
                max_width_cm=request.max_width_cm,
            )
        )
        shown = rank_by_preference(result.products, request.prefer_words)[:PRODUCTS_PER_SEARCH]
        with self._lock:
            self.stats.searches += 1
            self.stats.listings += result.offer_count
            self.stats.discarded += result.discarded_count
            self.products.update({product.id: product for product in shown})

        counts = ", ".join(
            [
                plural(result.offer_count, "listing"),
                plural(result.discarded_count, "discarded", "discarded"),
                plural(len(result.products), "product"),
            ]
        )
        return SearchOffersResult(
            summary=f'"{request.query}": {counts}',
            products=[_summary(product, request.prefer_words) for product in shown],
            stage_ms=result.stage_ms,
        )

    @recorded("measure")
    def check_fit(self, request: CheckFitInput) -> CheckFitResult:
        product = self.products.get(request.product_id)
        if product is None:
            raise ValueError(f"product {request.product_id} was not returned by search_offers")

        if product.width_cm is None:
            return CheckFitResult(summary=f"{product.name}: width unknown", verdict="unknown")
        if product.width_cm <= request.max_width_cm:
            return CheckFitResult(summary=f"{product.name}: fits", verdict="fits")
        return CheckFitResult(summary=f"{product.name}: does not fit", verdict="does_not_fit")

    @recorded("metrics")
    def category_metrics(self, request: CategoryMetricsInput) -> CategoryMetricsResult:
        stats = self._catalog.category_stats(request.category, self.market.country)
        summary = (
            f"no {request.category} data in {self.market.country.upper()} yet"
            if stats.avg_price is None
            else f"average {request.category} price: {self._money(stats.avg_price)}"
        )
        return CategoryMetricsResult(
            summary=summary,
            product_count=stats.product_count,
            avg_price=stats.avg_price,
            min_price=stats.min_price,
            max_price=stats.max_price,
        )

    def _money(self, value: float) -> str:
        return money(value, self.market.currency)


def _summary(product: Product, prefer_words: list[str]) -> ProductSummary:
    months = [o.installment_months for o in product.offers if o.installment_months]
    return ProductSummary(
        id=product.id,
        name=product.name,
        width_cm=product.width_cm,
        min_price=product.min_price,
        store_count=product.store_count,
        max_installments=max(months, default=None),
        matches_preferences=preference_matches(product.name, prefer_words) > 0,
    )
