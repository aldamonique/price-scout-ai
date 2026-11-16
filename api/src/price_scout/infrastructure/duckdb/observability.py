from datetime import UTC
from typing import Any

import duckdb

from price_scout.domain.errors import ObservabilityUnavailableError
from price_scout.domain.observability.models import (
    DailyUsage,
    FailedRun,
    LlmStats,
    Overview,
    RunStats,
    StageStats,
    ToolStats,
    VersionStats,
)
from price_scout.infrastructure.duckdb.connection import fetch_dicts

DAYS_SHOWN = 14
FAILURES_SHOWN = 5


class DuckDbObservability:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def overview(self) -> Overview:
        try:
            return Overview(
                runs=self._runs(),
                llm=self._llm(),
                by_version=[VersionStats.model_validate(row) for row in self._by_version()],
                daily=[DailyUsage.model_validate(row) for row in self._daily()],
                tools=[ToolStats.model_validate(row) for row in self._tools()],
                stages=[StageStats.model_validate(row) for row in self._stages()],
                recent_failures=[
                    FailedRun.model_validate(
                        {**row, "created_at": row["created_at"].replace(tzinfo=UTC)}
                    )
                    for row in self._failures()
                ],
            )
        except duckdb.CatalogException as error:
            raise ObservabilityUnavailableError(
                "The observability views are missing. Run dbt build in analytics/."
            ) from error

    def _query(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        cursor = self._connection.cursor()
        cursor.execute(sql, params or [])
        return fetch_dicts(cursor)

    def _runs(self) -> RunStats:
        row = self._query(
            """
            select
                count(*) as requests,
                count(*) filter (where status = 'done') as done,
                count(*) filter (where status = 'failed') as failed,
                count(*) filter (where status in ('queued', 'running')) as in_progress,
                avg(duration_s) filter (where status = 'done') as avg_duration_s,
                quantile_cont(duration_s, 0.95) filter (where status = 'done') as p95_duration_s,
                sum(cost_usd) as total_cost_usd,
                avg(cost_usd) filter (where status = 'done') as avg_cost_usd
            from gold_agent_runs
            """
        )[0]
        finished = row["done"] + row["failed"]
        return RunStats(**row, success_rate=row["done"] / finished if finished else None)

    def _llm(self) -> LlmStats:
        row = self._query(
            """
            select
                coalesce(sum(calls), 0) as calls,
                coalesce(sum(failed_calls), 0) as failed_calls,
                coalesce(sum(unpriced_calls), 0) as unpriced_calls,
                coalesce(sum(input_tokens), 0) as input_tokens,
                coalesce(sum(output_tokens), 0) as output_tokens,
                sum(cost_usd) as cost_usd,
                sum(avg_latency_ms * calls) / nullif(sum(calls), 0) as avg_latency_ms
            from gold_llm_versions
            """
        )[0]
        error_rate = row["failed_calls"] / row["calls"] if row["calls"] else None
        return LlmStats(**row, error_rate=error_rate)

    def _by_version(self) -> list[dict[str, Any]]:
        return self._query(
            "select * exclude (unpriced_calls) from gold_llm_versions order by task, calls desc"
        )

    def _daily(self) -> list[dict[str, Any]]:
        rows = self._query(
            """
            select
                day,
                sum(calls) as calls,
                sum(input_tokens) as input_tokens,
                sum(output_tokens) as output_tokens,
                sum(cost_usd) as cost_usd
            from gold_llm_usage_daily
            group by day
            order by day desc
            limit ?
            """,
            [DAYS_SHOWN],
        )
        return list(reversed(rows))

    def _tools(self) -> list[dict[str, Any]]:
        return self._query(
            """
            select
                tool,
                count(*) as calls,
                count(*) filter (where not ok) as failed_calls,
                avg(duration_ms) as avg_duration_ms,
                quantile_cont(duration_ms, 0.95) as p95_duration_ms
            from gold_agent_tool_steps
            group by tool
            order by calls desc
            """
        )

    def _stages(self) -> list[dict[str, Any]]:
        return self._query(
            """
            select
                stage,
                count(*) as searches,
                avg(duration_ms) as avg_ms,
                quantile_cont(duration_ms, 0.95) as p95_ms
            from gold_search_stages
            group by stage
            order by avg_ms desc
            """
        )

    def _failures(self) -> list[dict[str, Any]]:
        return self._query(
            """
            select request_id, description, error, created_at
            from gold_agent_runs
            where status = 'failed'
            order by created_at desc
            limit ?
            """,
            [FAILURES_SHOWN],
        )
