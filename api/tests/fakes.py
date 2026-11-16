from collections.abc import Callable
from datetime import UTC, datetime

from builders import product, shopping_request

from price_scout.application.search.search_offers import SearchOffers
from price_scout.application.shopping_request.ports import AgentTools
from price_scout.application.shopping_request.run_request import RunShoppingRequest
from price_scout.application.shopping_request.step_log import StepLog
from price_scout.application.shopping_request.tool_models import (
    CheckFitInput,
    PlanBudgetInput,
    SearchOffersInput,
)
from price_scout.application.shopping_request.toolbox import AgentToolbox
from price_scout.domain.catalog.models import (
    Category,
    CategoryStats,
    Offer,
    Product,
    RawSearch,
    SearchIntent,
)
from price_scout.domain.catalog.store_policy import StorePolicies
from price_scout.domain.errors import UpstreamError
from price_scout.domain.judgment.models import Judgment, ProductGroup
from price_scout.domain.observability.models import (
    LlmCall,
    LlmStats,
    Overview,
    RunStats,
)
from price_scout.domain.shopping_request.models import (
    AgentPlan,
    AgentUsage,
    BudgetLine,
    PlanChoice,
    RequestSummary,
    ShoppingRequest,
)

OFFERS = [
    Offer(offer_id="o1", title="Sofá 3 Lugares", store="Store A", price=1299),
    Offer(offer_id="o2", title="Capa de Sofá", store="Store B", price=99),
]


class FakeOfferSource:
    def fetch(self, intent: SearchIntent) -> RawSearch:
        return RawSearch(
            search_id="abc",
            query=intent.query,
            country=intent.market.country,
            fetched_at=datetime.now(UTC),
            payload={},
        )


class FakeRawStore:
    def __init__(self) -> None:
        self.saved: list[RawSearch] = []

    def save(self, raw: RawSearch) -> None:
        self.saved.append(raw)

    def load(self, search_id: str) -> RawSearch | None:
        return next((raw for raw in self.saved if raw.search_id == search_id), None)


class FakeOfferJudge:
    def __init__(self, version: str = "fake/v1") -> None:
        self.calls = 0
        self.version = version
        self.seen: list[str] = []

    def judge(self, intent: SearchIntent, offers: list[Offer]) -> Judgment:
        self.calls += 1
        self.seen = [offer.offer_id for offer in offers]
        group = ProductGroup(
            name="3-Seat Sofa",
            category="furniture",
            width_cm=205,
            depth_cm=None,
            height_cm=None,
            offer_ids=["o1"],
        )
        return Judgment(products=[group], discarded=[])


class FakeJudgmentRepository:
    def __init__(self) -> None:
        self.judgments: dict[str, Judgment] = {}
        self.versions: dict[str, str] = {}

    def is_judged(self, search_id: str, version: str) -> bool:
        return self.versions.get(search_id) == version

    def save(self, search_id: str, judgment: Judgment, version: str) -> None:
        self.judgments[search_id] = judgment
        self.versions[search_id] = version

    def discarded_count(self, search_id: str) -> int:
        return len(self.judgments[search_id].discarded)


class FakeCatalog:
    def offers(self, search_id: str) -> list[Offer]:
        return OFFERS

    def products(self, search_id: str, intent: SearchIntent) -> list[Product]:
        return [product(f"{search_id}-p1")]

    def category_stats(self, category: Category, country: str) -> CategoryStats:
        return CategoryStats(
            category=category,
            country=country,
            product_count=4,
            avg_price=1180,
            min_price=899,
            max_price=1499,
        )


class InMemoryShoppingRequestRepository:
    def __init__(self) -> None:
        self.requests: dict[str, ShoppingRequest] = {}
        self.history: list[ShoppingRequest] = []

    def save(self, request: ShoppingRequest) -> None:
        self.requests[request.id] = request
        self.history.append(request)

    def delete(self, request_id: str) -> None:
        self.requests.pop(request_id, None)

    def get(self, request_id: str) -> ShoppingRequest | None:
        return self.requests.get(request_id)

    def recent(self, limit: int) -> list[RequestSummary]:
        newest = sorted(self.requests.values(), key=lambda r: r.created_at, reverse=True)
        return [
            RequestSummary(
                id=r.id,
                description=r.description,
                market=r.market,
                budget=r.budget,
                status=r.status,
                total=r.plan.total if r.plan else None,
                item_count=len(r.plan.items) if r.plan else 0,
                created_at=r.created_at,
            )
            for r in newest[:limit]
        ]

    def requeue_unfinished(self) -> list[str]:
        unfinished = [r for r in self.requests.values() if r.status in ("queued", "running")]
        for request in unfinished:
            self.save(request.model_copy(update={"status": "queued", "steps": []}))
        return [request.id for request in sorted(unfinished, key=lambda r: r.created_at)]

    def count_since(self, moment: datetime) -> int:
        return sum(1 for request in self.requests.values() if request.created_at >= moment)


class InlineJobRunner:
    def submit(self, job: Callable[[], None]) -> None:
        job()


class ScriptedAgent:
    def __init__(self, product_id: str = "abc-p1") -> None:
        self._product_id = product_id

    def run(self, request: ShoppingRequest, tools: AgentTools) -> tuple[AgentPlan, AgentUsage]:
        tools.plan_budget(PlanBudgetInput(lines=[BudgetLine(item="Sofa", amount=2800)]))
        tools.search_offers(
            SearchOffersInput(
                query="sofá 3 lugares",
                category="furniture",
                max_price=2800,
                max_width_cm=210,
                prefer_words=[],
            )
        )
        tools.check_fit(CheckFitInput(product_id="abc-p1", max_width_cm=210))
        choice = PlanChoice(
            item="Sofa",
            product_id=self._product_id,
            reason="It fits.",
            max_width_cm=210,
            differences=None,
        )
        plan = AgentPlan(choices=[choice], unmet=[])
        return plan, AgentUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)


class FailingAgent:
    def run(self, request: ShoppingRequest, tools: AgentTools) -> tuple[AgentPlan, AgentUsage]:
        raise UpstreamError("SerpApi failed: ConnectTimeout")


def new_search_offers(
    store_policies: StorePolicies | None = None,
) -> tuple[SearchOffers, FakeRawStore, FakeOfferJudge, FakeJudgmentRepository]:
    raw_store, judge, judgments = FakeRawStore(), FakeOfferJudge(), FakeJudgmentRepository()
    search = SearchOffers(
        FakeOfferSource(), raw_store, judge, judgments, FakeCatalog(), store_policies
    )
    return search, raw_store, judge, judgments


def new_toolbox(
    step_log: StepLog | None = None, request: ShoppingRequest | None = None
) -> AgentToolbox:

    request = request or shopping_request()
    search, _, _, _ = new_search_offers()
    return AgentToolbox(
        search, FakeCatalog(), step_log or StepLog(), request.market, request.budget
    )


def new_run_request(
    agent: ScriptedAgent | FailingAgent, requests: InMemoryShoppingRequestRepository
) -> RunShoppingRequest:
    return RunShoppingRequest(agent, new_toolbox, requests)


class InMemoryCallLog:
    def __init__(self) -> None:
        self.recorded: list[LlmCall] = []

    def record(self, call: LlmCall) -> None:
        self.recorded.append(call)

    def calls(self, request_id: str) -> list[LlmCall]:
        return [call for call in self.recorded if call.request_id == request_id]

    def delete_for_request(self, request_id: str) -> None:
        self.recorded = [call for call in self.recorded if call.request_id != request_id]


EMPTY_OVERVIEW = Overview(
    runs=RunStats(
        requests=0,
        done=0,
        failed=0,
        in_progress=0,
        success_rate=None,
        avg_duration_s=None,
        p95_duration_s=None,
        total_cost_usd=None,
        avg_cost_usd=None,
    ),
    llm=LlmStats(
        calls=0,
        failed_calls=0,
        unpriced_calls=0,
        error_rate=None,
        input_tokens=0,
        output_tokens=0,
        cost_usd=None,
        avg_latency_ms=None,
    ),
    by_version=[],
    daily=[],
    tools=[],
    stages=[],
    recent_failures=[],
)


class FakeObservabilityReader:
    def __init__(self, overview: Overview = EMPTY_OVERVIEW) -> None:
        self._overview = overview

    def overview(self) -> Overview:
        return self._overview
