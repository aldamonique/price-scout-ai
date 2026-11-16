from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest
from builders import shopping_request
from dbt_views import create_gold_views

from price_scout.domain.errors import ObservabilityUnavailableError
from price_scout.domain.observability.models import LlmCall
from price_scout.domain.shopping_request.models import AgentStep
from price_scout.infrastructure.duckdb.call_log import DuckDbCallLog
from price_scout.infrastructure.duckdb.connection import open_warehouse
from price_scout.infrastructure.duckdb.observability import DuckDbObservability
from price_scout.infrastructure.duckdb.shopping_request_repository import (
    DuckDbShoppingRequestRepository,
)

START = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)
GOLD = (
    "gold_llm_usage_daily",
    "gold_llm_versions",
    "gold_agent_runs",
    "gold_agent_tool_steps",
    "gold_search_stages",
)


@pytest.fixture
def connection(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    return open_warehouse(tmp_path)


def call(
    call_id: str,
    request_id: str | None,
    task: str = "agent",
    latency_ms: int = 1000,
    cost_usd: float | None = 0.01,
    ok: bool = True,
) -> LlmCall:
    return LlmCall.model_validate(
        {
            "id": call_id,
            "request_id": request_id,
            "task": task,
            "model": "agent-model" if task == "agent" else "judge-model",
            "prompt_version": "v3" if task == "agent" else "v1",
            "input_tokens": 1000,
            "output_tokens": 100,
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
            "ok": ok,
            "error": None if ok else "timeout",
            "created_at": START,
        }
    )


def step(number: int, tool: str, ok: bool = True) -> AgentStep:
    stages = {"fetch": 1000 * number, "judge": 3000 * number} if tool == "search_offers" else None
    return AgentStep(
        number=number,
        kind="search",
        tool=tool,
        summary="",
        duration_ms=100 * number,
        ok=ok,
        stage_ms=stages,
    )


def seed(connection: duckdb.DuckDBPyConnection) -> None:
    requests = DuckDbShoppingRequestRepository(connection)
    requests.save(
        shopping_request("r1").model_copy(
            update={
                "status": "done",
                "steps": [step(1, "plan_budget"), step(2, "search_offers")],
                "updated_at": shopping_request().created_at + timedelta(seconds=30),
            }
        )
    )
    requests.save(
        shopping_request("r2").model_copy(
            update={
                "status": "failed",
                "error": "SerpApi failed",
                "steps": [step(1, "search_offers", ok=False)],
            }
        )
    )
    log = DuckDbCallLog(connection)
    log.record(call("c1", "r1"))
    log.record(call("c2", "r1", task="judge", latency_ms=3000, cost_usd=None))
    log.record(call("c3", "r2", ok=False))


def test_calls_are_read_back_per_request_in_order(connection: duckdb.DuckDBPyConnection) -> None:
    log = DuckDbCallLog(connection)
    log.record(call("c1", "r1"))
    log.record(call("c2", "r2"))

    assert [c.id for c in log.calls("r1")] == ["c1"]
    assert log.calls("r1")[0] == call("c1", "r1")


def test_the_overview_reads_the_dbt_gold_models(connection: duckdb.DuckDBPyConnection) -> None:
    seed(connection)
    create_gold_views(connection, *GOLD)

    overview = DuckDbObservability(connection).overview()

    runs = overview.runs
    assert (runs.requests, runs.done, runs.failed, runs.success_rate) == (2, 1, 1, 0.5)
    assert runs.avg_duration_s == pytest.approx(30)
    assert runs.total_cost_usd == pytest.approx(0.02)

    llm = overview.llm
    assert (llm.calls, llm.failed_calls, llm.unpriced_calls) == (3, 1, 1)
    assert llm.error_rate == pytest.approx(1 / 3)
    assert llm.avg_latency_ms == pytest.approx(5000 / 3)

    assert [(v.task, v.calls) for v in overview.by_version] == [("agent", 2), ("judge", 1)]
    assert [(d.day.isoformat(), d.calls) for d in overview.daily] == [("2026-11-16", 3)]
    assert [(t.tool, t.calls, t.failed_calls) for t in overview.tools] == [
        ("search_offers", 2, 1),
        ("plan_budget", 1, 0),
    ]
    assert [(s.stage, s.searches, s.avg_ms) for s in overview.stages] == [
        ("judge", 2, 4500),
        ("fetch", 2, 1500),
    ]
    assert [(f.request_id, f.error) for f in overview.recent_failures] == [("r2", "SerpApi failed")]


def test_an_empty_warehouse_has_an_empty_overview(connection: duckdb.DuckDBPyConnection) -> None:
    create_gold_views(connection, *GOLD)

    overview = DuckDbObservability(connection).overview()

    assert (overview.runs.requests, overview.runs.success_rate) == (0, None)
    assert (overview.llm.calls, overview.llm.error_rate) == (0, None)


def test_missing_views_say_how_to_fix_it(connection: duckdb.DuckDBPyConnection) -> None:
    with pytest.raises(ObservabilityUnavailableError, match="dbt build"):
        DuckDbObservability(connection).overview()


def test_calls_of_a_request_can_be_deleted(connection: duckdb.DuckDBPyConnection) -> None:
    log = DuckDbCallLog(connection)
    log.record(call("c1", "r1"))
    log.record(call("c2", "r2"))

    log.delete_for_request("r1")

    assert (log.calls("r1"), [c.id for c in log.calls("r2")]) == ([], ["c2"])
