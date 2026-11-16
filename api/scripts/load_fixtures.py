import shutil
from datetime import UTC, datetime, timedelta

from price_scout.config import REPO_ROOT, Settings
from price_scout.domain.catalog.markets import market_for
from price_scout.domain.catalog.models import Product, StoreOffer
from price_scout.domain.judgment.models import DiscardedOffer, Judgment, ProductGroup
from price_scout.domain.observability.models import LlmCall
from price_scout.domain.shopping_request.models import (
    AgentStep,
    AgentUsage,
    PlanItem,
    Preferences,
    SearchStats,
    ShoppingPlan,
    ShoppingRequest,
)
from price_scout.infrastructure.duckdb.call_log import DuckDbCallLog
from price_scout.infrastructure.duckdb.connection import open_warehouse
from price_scout.infrastructure.duckdb.judgment_repository import DuckDbJudgmentRepository
from price_scout.infrastructure.duckdb.shopping_request_repository import (
    DuckDbShoppingRequestRepository,
)

FIXTURES = REPO_ROOT / "analytics" / "fixtures" / "bronze"
START = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)
BRAZIL = market_for("br")
JUDGE_VERSION = "ci-judge/v2/glossary"


def group(name: str, category: str, *offer_ids: str) -> ProductGroup:
    return ProductGroup.model_validate(
        {
            "name": name,
            "category": category,
            "width_cm": None,
            "depth_cm": None,
            "height_cm": None,
            "offer_ids": list(offer_ids),
        }
    )


JUDGMENTS = {
    "ci-keyboard": Judgment(
        products=[
            group("Redragon Kumara Pink Mechanical Keyboard", "electronics", "o1", "o2", "o3")
        ],
        discarded=[DiscardedOffer(offer_id="o4", reason="keycaps, not a keyboard")],
    ),
    "ci-book": Judgment(
        products=[
            group("Mrs Dalloway, paperback", "books", "o1", "o2"),
            group("Mrs Dalloway, e-book", "books", "o3"),
        ],
        discarded=[],
    ),
}

KEYBOARD = Product(
    id="ci-keyboard-p1",
    name="Redragon Kumara Pink Mechanical Keyboard",
    category="electronics",
    min_price=249.9,
    store_count=2,
    offers=[StoreOffer(store="KaBuM!", price=249.9), StoreOffer(store="Amazon", price=279.0)],
)


def steps() -> list[AgentStep]:
    return [
        AgentStep(
            number=1, kind="plan", tool="plan_budget", summary="1 item", duration_ms=3, ok=True
        ),
        AgentStep(
            number=2,
            kind="search",
            tool="search_offers",
            summary='"teclado mecânico rosa": 8 listings',
            duration_ms=4200,
            ok=True,
            stage_ms={"fetch": 1800, "silver": 120, "judge": 2100, "gold": 180},
        ),
        AgentStep(
            number=3,
            kind="search",
            tool="search_offers",
            summary="error: SerpApi returned no listings",
            duration_ms=900,
            ok=False,
        ),
    ]


def requests() -> list[ShoppingRequest]:
    plan = ShoppingPlan(
        market=BRAZIL,
        budget=None,
        total=249.9,
        leftover=None,
        items=[
            PlanItem(item="Mechanical keyboard", product=KEYBOARD, reason="Pink.", savings=29.1)
        ],
        unmet=[],
        insights=[],
        stats=SearchStats(searches=2, listings=8, discarded=1),
        usage=AgentUsage(agent_model="ci-agent", agent_prompt_version="v6"),
    )
    base = {"market": BRAZIL, "preferences": Preferences(colors="pink"), "created_at": START}
    return [
        ShoppingRequest(
            id="ci-done",
            description="A pink mechanical keyboard",
            budget=None,
            status="done",
            steps=steps(),
            plan=plan,
            updated_at=START + timedelta(seconds=42),
            **base,
        ),
        ShoppingRequest(
            id="ci-failed",
            description="A book",
            budget=50,
            status="failed",
            error="SerpApi failed (401): Invalid API key",
            updated_at=START + timedelta(seconds=3),
            **base,
        ),
        ShoppingRequest(
            id="ci-queued",
            description="Coffee beans",
            budget=None,
            status="queued",
            updated_at=START,
            **base,
        ),
    ]


def calls() -> list[LlmCall]:
    common = {"model": "ci-model", "error": None, "created_at": START}
    return [
        LlmCall(
            id="ci-call-1",
            request_id="ci-done",
            task="agent",
            prompt_version="v6",
            input_tokens=1200,
            output_tokens=180,
            cost_usd=0.004,
            latency_ms=2300,
            ok=True,
            **common,
        ),
        LlmCall(
            id="ci-call-2",
            request_id="ci-done",
            task="judge",
            prompt_version="v2",
            input_tokens=3300,
            output_tokens=650,
            cost_usd=0.002,
            latency_ms=2100,
            ok=True,
            **common,
        ),
        LlmCall(
            id="ci-call-3",
            request_id=None,
            task="judge",
            prompt_version="v2",
            input_tokens=0,
            output_tokens=0,
            cost_usd=None,
            latency_ms=30000,
            ok=False,
            **{**common, "error": "APITimeoutError"},
        ),
    ]


def main() -> None:
    settings = Settings()
    bronze = settings.data_dir / "bronze"
    bronze.mkdir(parents=True, exist_ok=True)
    for path in FIXTURES.glob("*.json"):
        shutil.copy(path, bronze / path.name)

    connection = open_warehouse(settings.data_dir)
    judgments = DuckDbJudgmentRepository(connection)
    for search_id, judgment in JUDGMENTS.items():
        judgments.save(search_id, judgment, JUDGE_VERSION)
    shopping_requests = DuckDbShoppingRequestRepository(connection)
    for request in requests():
        shopping_requests.save(request)
    call_log = DuckDbCallLog(connection)
    for call in calls():
        call_log.record(call)
    connection.close()
    print(f"fixtures loaded into {settings.data_dir}")


if __name__ == "__main__":
    main()
