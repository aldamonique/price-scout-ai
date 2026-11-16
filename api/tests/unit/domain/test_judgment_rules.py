from price_scout.domain.catalog.models import Offer
from price_scout.domain.judgment.models import DiscardedOffer, Judgment, ProductGroup
from price_scout.domain.judgment.rules import UNCLASSIFIED, reconcile


def offer(offer_id: str) -> Offer:
    return Offer(offer_id=offer_id, title="Sofá", store="Store", price=1000)


def group(*offer_ids: str) -> ProductGroup:
    return ProductGroup(
        name="Sofa",
        category="furniture",
        width_cm=None,
        depth_cm=None,
        height_cm=None,
        offer_ids=list(offer_ids),
    )


def test_drops_ids_the_model_made_up() -> None:
    judgment = Judgment(products=[group("o1", "o99")], discarded=[])

    result = reconcile(judgment, [offer("o1")])

    assert result.products[0].offer_ids == ["o1"]


def test_keeps_a_listing_only_in_its_first_group() -> None:
    judgment = Judgment(products=[group("o1"), group("o1", "o2")], discarded=[])

    result = reconcile(judgment, [offer("o1"), offer("o2")])

    assert [g.offer_ids for g in result.products] == [["o1"], ["o2"]]


def test_discards_listings_the_model_forgot() -> None:
    judgment = Judgment(
        products=[group("o1")], discarded=[DiscardedOffer(offer_id="o2", reason="cover")]
    )

    result = reconcile(judgment, [offer("o1"), offer("o2"), offer("o3")])

    assert [d.offer_id for d in result.discarded] == ["o2", "o3"]
    assert result.discarded[1].reason == UNCLASSIFIED


def test_removes_groups_left_empty() -> None:
    judgment = Judgment(products=[group("o99")], discarded=[])

    assert reconcile(judgment, [offer("o1")]).products == []
