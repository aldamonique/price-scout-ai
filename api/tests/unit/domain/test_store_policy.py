from pathlib import Path

import pytest

from price_scout.domain.catalog.models import Offer
from price_scout.domain.catalog.store_policy import StorePolicy
from price_scout.infrastructure.context import load_store_policies

POLICY = StorePolicy(blocked=("AliExpress", "eBay", "Wish", "LightInTheBox"))


def test_a_store_matches_by_its_first_words_ignoring_case_and_punctuation() -> None:
    assert POLICY.blocks("AliExpress.com")
    assert POLICY.blocks("eBay - seller123")
    assert POLICY.blocks("EBAY")
    assert POLICY.blocks("Wish")
    assert POLICY.blocks("lightinthebox.com")


def test_a_store_that_only_contains_a_blocked_word_is_allowed() -> None:
    assert not POLICY.blocks("Wishop Brasil")
    assert not POLICY.blocks("Loja do eBay Fan")
    assert not POLICY.blocks("Mercado Livre")
    assert not POLICY.blocks("")


def test_split_keeps_the_order_of_the_offers() -> None:
    offers = [
        Offer(offer_id=offer_id, title="Fone", store=store, price=200)
        for offer_id, store in [("o1", "KaBuM!"), ("o2", "eBay"), ("o3", "Amazon")]
    ]

    allowed, blocked = POLICY.split(offers)

    assert [o.offer_id for o in allowed] == ["o1", "o3"]
    assert [o.offer_id for o in blocked] == ["o2"]


def test_the_version_changes_only_when_the_list_changes() -> None:
    same = StorePolicy(blocked=("ebay", "Wish", "AliExpress", "LightInTheBox"))

    assert same.version == POLICY.version
    assert StorePolicy(blocked=("eBay",)).version != POLICY.version


def test_the_shipped_policies_follow_each_market() -> None:
    policies = load_store_policies()
    brazil, us = policies.for_country("BR"), policies.for_country("us")

    assert brazil.blocks("AliExpress") and brazil.blocks("eBay") and brazil.blocks("Temu")
    assert not brazil.blocks("Mercado Livre") and not brazil.blocks("Amazon.com.br")
    assert "Brazil" in brazil.reason
    assert us.blocks("AliExpress") and not us.blocks("eBay")


def test_a_market_can_allow_a_store_the_default_blocks(tmp_path: Path) -> None:
    path = tmp_path / "stores.yml"
    path.write_text(
        "default: {reason: far away, blocked: [Temu, Shein]}\n"
        "markets: {us: {allowed: [shein], also_blocked: [Fake Shop]}}\n",
        encoding="utf-8",
    )

    us = load_store_policies(path).for_country("us")

    assert us.blocks("Temu") and us.blocks("Fake Shop") and not us.blocks("Shein")
    assert us.reason == "far away"


def test_an_unknown_market_in_the_file_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "stores.yml"
    path.write_text(
        "default: {reason: x, blocked: []}\nmarkets: {brasil: {also_blocked: [eBay]}}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown market 'brasil'"):
        load_store_policies(path)
