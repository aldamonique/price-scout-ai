from datetime import timedelta
from pathlib import Path

import duckdb
import pytest
from builders import shopping_request

from price_scout.domain.judgment.models import DiscardedOffer, Judgment, ProductGroup
from price_scout.domain.shopping_request.models import AgentStep, Preferences
from price_scout.infrastructure.duckdb.connection import open_warehouse
from price_scout.infrastructure.duckdb.judgment_repository import DuckDbJudgmentRepository
from price_scout.infrastructure.duckdb.shopping_request_repository import (
    DuckDbShoppingRequestRepository,
)


@pytest.fixture
def connection(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    return open_warehouse(tmp_path)


def test_judgment_is_saved_and_replaced(connection: duckdb.DuckDBPyConnection) -> None:
    repository = DuckDbJudgmentRepository(connection)
    group = ProductGroup(
        name="Sofa",
        category="furniture",
        width_cm=205,
        depth_cm=None,
        height_cm=None,
        offer_ids=["o1"],
    )
    discarded = [DiscardedOffer(offer_id="o2", reason="cover")]

    repository.save("s1", Judgment(products=[group], discarded=discarded), "m/v1")
    repository.save("s1", Judgment(products=[group], discarded=discarded), "m/v2")

    assert repository.is_judged("s1", "m/v2")
    assert not repository.is_judged("s1", "m/v1")
    assert repository.discarded_count("s1") == 1
    assert not repository.is_judged("s2", "m/v2")


def test_shopping_request_round_trip_with_steps(connection: duckdb.DuckDBPyConnection) -> None:
    repository = DuckDbShoppingRequestRepository(connection)
    step = AgentStep(
        number=1, kind="plan", tool="plan_budget", summary="1 item", duration_ms=3, ok=True
    )
    saved = shopping_request(preferences=Preferences(colors="gray")).model_copy(
        update={"status": "running", "steps": [step]}
    )

    repository.save(saved)

    assert repository.get("r1") == saved
    assert repository.get("missing") is None


def test_unfinished_requests_are_queued_again_after_a_restart(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    repository = DuckDbShoppingRequestRepository(connection)
    step = AgentStep(number=1, kind="plan", tool="plan_budget", summary="", duration_ms=1, ok=True)
    repository.save(
        shopping_request("r1").model_copy(update={"status": "running", "steps": [step]})
    )
    repository.save(shopping_request("r2").model_copy(update={"status": "done"}))

    assert repository.requeue_unfinished() == ["r1"]

    requeued = repository.get("r1")
    assert requeued is not None
    assert (requeued.status, requeued.steps) == ("queued", [])


def test_requests_are_counted_since_a_moment(connection: duckdb.DuckDBPyConnection) -> None:
    repository = DuckDbShoppingRequestRepository(connection)
    first = shopping_request("r1")
    repository.save(first)
    repository.save(
        shopping_request("r2").model_copy(
            update={"created_at": first.created_at + timedelta(hours=2)}
        )
    )

    assert repository.count_since(first.created_at + timedelta(hours=1)) == 1


def test_recent_lists_newest_first_with_plan_totals(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    repository = DuckDbShoppingRequestRepository(connection)
    older = shopping_request("r1")
    newer = shopping_request("r2").model_copy(
        update={"created_at": older.created_at + timedelta(minutes=5)}
    )
    repository.save(older)
    repository.save(newer)

    summaries = repository.recent(limit=10)

    assert [s.id for s in summaries] == ["r2", "r1"]
    assert (summaries[0].total, summaries[0].item_count) == (None, 0)
    assert repository.recent(limit=1)[0].id == "r2"


def test_a_request_without_budget_is_saved_and_deleted(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    repository = DuckDbShoppingRequestRepository(connection)
    repository.save(shopping_request("r1", budget=None))

    assert repository.get("r1") == shopping_request("r1", budget=None)
    assert repository.recent(limit=5)[0].budget is None

    repository.delete("r1")

    assert repository.get("r1") is None


def test_an_old_warehouse_accepts_requests_without_budget(tmp_path: Path) -> None:
    old = duckdb.connect(str(tmp_path / "warehouse.duckdb"))
    old.execute(
        "create table shopping_requests (id varchar primary key, description varchar not null,"
        " market json not null, budget double not null, preferences json not null,"
        " status varchar not null, steps json not null, plan json, error varchar,"
        " created_at timestamp not null, updated_at timestamp not null)"
    )
    old.close()

    repository = DuckDbShoppingRequestRepository(open_warehouse(tmp_path))
    repository.save(shopping_request("r1", budget=None))

    assert repository.get("r1") is not None
