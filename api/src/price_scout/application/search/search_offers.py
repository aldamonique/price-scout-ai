import time

from price_scout.domain.catalog.models import SearchIntent, SearchResult
from price_scout.domain.catalog.ports import Catalog, OfferSource, RawStore
from price_scout.domain.catalog.store_policy import StorePolicies
from price_scout.domain.judgment.models import Judgment
from price_scout.domain.judgment.ports import JudgmentRepository, OfferJudge
from price_scout.domain.judgment.rules import discard_blocked, reconcile


class StageTimer:
    def __init__(self) -> None:
        self.stage_ms: dict[str, int] = {}
        self._started = time.perf_counter()

    def lap(self, stage: str) -> None:
        now = time.perf_counter()
        self.stage_ms[stage] = round((now - self._started) * 1000)
        self._started = now


class SearchOffers:
    def __init__(
        self,
        offer_source: OfferSource,
        raw_store: RawStore,
        offer_judge: OfferJudge,
        judgments: JudgmentRepository,
        catalog: Catalog,
        store_policies: StorePolicies | None = None,
    ) -> None:
        self._offer_source = offer_source
        self._raw_store = raw_store
        self._offer_judge = offer_judge
        self._judgments = judgments
        self._catalog = catalog
        self._store_policies = store_policies or StorePolicies()

    def execute(self, intent: SearchIntent) -> SearchResult:
        timer = StageTimer()
        raw = self._offer_source.fetch(intent)
        self._raw_store.save(raw)
        timer.lap("fetch")

        offers = self._catalog.offers(raw.search_id)
        timer.lap("silver")

        policy = self._store_policies.for_country(intent.market.country)
        version = f"{self._offer_judge.version}/{policy.version}"
        if not self._judgments.is_judged(raw.search_id, version):
            allowed, blocked = policy.split(offers)
            judgment = (
                self._offer_judge.judge(intent, allowed)
                if allowed
                else Judgment(products=[], discarded=[])
            )
            complete = discard_blocked(reconcile(judgment, allowed), blocked, policy.reason)
            self._judgments.save(raw.search_id, complete, version)
        timer.lap("judge")

        products = self._catalog.products(raw.search_id, intent)
        discarded = self._judgments.discarded_count(raw.search_id)
        timer.lap("gold")

        return SearchResult(
            search_id=raw.search_id,
            offer_count=len(offers),
            discarded_count=discarded,
            products=products,
            stage_ms=timer.stage_ms,
        )
