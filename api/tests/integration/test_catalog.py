from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest
from builders import BRAZIL

from price_scout.config import REPO_ROOT
from price_scout.domain.catalog.models import RawSearch, SearchIntent
from price_scout.domain.judgment.models import DiscardedOffer, Judgment, ProductGroup
from price_scout.infrastructure.duckdb.catalog import DuckDbCatalog
from price_scout.infrastructure.duckdb.connection import open_warehouse
from price_scout.infrastructure.duckdb.judgment_repository import DuckDbJudgmentRepository
from price_scout.infrastructure.duckdb.medallion import MedallionSql
from price_scout.infrastructure.lake.raw_store import FileRawStore

LISTINGS = [
    {"position": 1, "title": "Teclado Mecânico Rosa", "source": "KaBuM!", "extracted_price": 249.9},
    {"position": 2, "title": "Teclado Mecânico Rosa", "source": "Amazon", "extracted_price": 279.0},
    {"position": 3, "title": "Teclado Mecânico Rosa", "source": "Amazon", "extracted_price": 289.0},
    {"position": 4, "title": "Keycaps rosa", "source": "Shopee", "extracted_price": 59.9},
    {"position": 5, "title": "Sem preço", "source": "Loja"},
]


@pytest.fixture
def catalog(tmp_path: Path) -> DuckDbCatalog:
    connection: duckdb.DuckDBPyConnection = open_warehouse(tmp_path)
    bronze = tmp_path / "bronze"
    FileRawStore(bronze).save(
        RawSearch(
            search_id="s1",
            query="teclado mecânico rosa",
            country="br",
            fetched_at=datetime(2026, 11, 16, 12, 0, tzinfo=UTC),
            payload={"shopping_results": LISTINGS},
        )
    )
    (bronze / "broken.json").write_text("not json", encoding="utf-8")

    keyboard = ProductGroup(
        name="Pink Mechanical Keyboard",
        category="electronics",
        width_cm=None,
        depth_cm=None,
        height_cm=None,
        offer_ids=["o1", "o2", "o3"],
    )
    judgment = Judgment(products=[keyboard], discarded=[DiscardedOffer(offer_id="o4", reason="")])
    DuckDbJudgmentRepository(connection).save("s1", judgment, "judge/v2")

    return DuckDbCatalog(
        connection,
        MedallionSql(REPO_ROOT / "analytics"),
        lambda search_id: (bronze / f"{search_id}.json").as_posix(),
    )


def test_silver_reads_only_the_file_of_the_search(catalog: DuckDbCatalog) -> None:
    offers = catalog.offers("s1")

    assert [(offer.offer_id, offer.price) for offer in offers] == [
        ("o4", 59.9),
        ("o1", 249.9),
        ("o2", 279.0),
        ("o3", 289.0),
    ]


def test_gold_keeps_the_cheapest_offer_per_store(catalog: DuckDbCatalog) -> None:
    intent = SearchIntent(query="teclado", category="electronics", market=BRAZIL)

    [product] = catalog.products("s1", intent)

    assert (product.name, product.min_price, product.store_count) == (
        "Pink Mechanical Keyboard",
        249.9,
        2,
    )
    assert [(offer.store, offer.price) for offer in product.offers] == [
        ("KaBuM!", 249.9),
        ("Amazon", 279.0),
    ]


def test_gold_applies_the_price_limit(catalog: DuckDbCatalog) -> None:
    intent = SearchIntent(query="teclado", category="electronics", market=BRAZIL, max_price=200)

    assert catalog.products("s1", intent) == []
