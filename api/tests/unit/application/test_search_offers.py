from builders import BRAZIL
from fakes import (
    FakeCatalog,
    FakeJudgmentRepository,
    FakeOfferJudge,
    FakeOfferSource,
    FakeRawStore,
    new_search_offers,
)

from price_scout.application.search.search_offers import SearchOffers
from price_scout.domain.catalog.models import SearchIntent
from price_scout.domain.catalog.store_policy import StorePolicies, StorePolicy

INTENT = SearchIntent(query="sofá 3 lugares", category="furniture", market=BRAZIL, max_price=2500)


def test_returns_products_and_counts() -> None:
    search, _, _, _ = new_search_offers()

    result = search.execute(INTENT)

    assert [p.id for p in result.products] == ["abc-p1"]
    assert (result.offer_count, result.discarded_count) == (2, 1)


def test_saves_the_raw_search_to_bronze() -> None:
    search, raw_store, _, _ = new_search_offers()

    search.execute(INTENT)

    assert [raw.search_id for raw in raw_store.saved] == ["abc"]


def test_listings_the_judge_forgot_are_saved_as_discarded() -> None:
    search, _, _, judgments = new_search_offers()

    search.execute(INTENT)

    assert [d.offer_id for d in judgments.judgments["abc"].discarded] == ["o2"]


def test_does_not_judge_the_same_search_twice() -> None:
    search, _, judge, _ = new_search_offers()

    search.execute(INTENT)
    search.execute(INTENT)

    assert judge.calls == 1


def test_a_new_judge_version_judges_the_search_again() -> None:
    search, _, judge, judgments = new_search_offers()
    search.execute(INTENT)

    judge.version = "fake/v2"
    search.execute(INTENT)

    assert judge.calls == 2
    assert judgments.versions["abc"].startswith("fake/v2/stores-")


def test_each_stage_of_the_search_is_timed() -> None:
    search, _, _, _ = new_search_offers()

    result = search.execute(INTENT)

    assert list(result.stage_ms) == ["fetch", "silver", "judge", "gold"]
    assert all(ms >= 0 for ms in result.stage_ms.values())


def test_listings_from_blocked_stores_never_reach_the_judge() -> None:
    policy = StorePolicy(blocked=("Store B",), reason="cross-border marketplace")
    search, _, judge, judgments = new_search_offers(StorePolicies(by_country={"br": policy}))

    search.execute(INTENT)

    assert judge.seen == ["o1"]
    [blocked] = judgments.judgments["abc"].discarded
    assert (blocked.offer_id, blocked.reason) == ("o2", "Store B: cross-border marketplace")


def test_changing_the_blocked_stores_judges_the_search_again() -> None:
    judge, judgments = FakeOfferJudge(), FakeJudgmentRepository()

    def search(policy: StorePolicy) -> SearchOffers:
        policies = StorePolicies(default=policy)
        return SearchOffers(
            FakeOfferSource(), FakeRawStore(), judge, judgments, FakeCatalog(), policies
        )

    search(StorePolicy(blocked=("eBay",))).execute(INTENT)
    search(StorePolicy(blocked=("eBay",))).execute(INTENT)
    search(StorePolicy(blocked=("eBay", "Temu"))).execute(INTENT)

    assert judge.calls == 2


def test_each_market_uses_its_own_blocked_stores() -> None:
    policies = StorePolicies(
        default=StorePolicy(blocked=("Store B",)), by_country={"br": StorePolicy()}
    )
    search, _, judge, _ = new_search_offers(policies)

    search.execute(INTENT)

    assert judge.seen == ["o1", "o2"]
