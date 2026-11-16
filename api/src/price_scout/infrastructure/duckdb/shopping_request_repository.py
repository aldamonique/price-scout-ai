from datetime import UTC, datetime
from typing import Any

import duckdb
from pydantic import TypeAdapter

from price_scout.domain.catalog.models import Market
from price_scout.domain.shopping_request.models import (
    AgentStep,
    Preferences,
    RequestSummary,
    ShoppingPlan,
    ShoppingRequest,
)
from price_scout.infrastructure.duckdb.connection import fetch_dicts

STEPS = TypeAdapter(list[AgentStep])


class DuckDbShoppingRequestRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def save(self, request: ShoppingRequest) -> None:
        self._connection.cursor().execute(
            """
            insert or replace into shopping_requests (
                id, description, market, budget, preferences, status, steps, plan, error,
                created_at, updated_at
            ) values (
                $id, $description, $market, $budget, $preferences, $status, $steps, $plan,
                $error, $created_at, $updated_at
            )
            """,
            {
                "id": request.id,
                "description": request.description,
                "market": request.market.model_dump_json(),
                "budget": request.budget,
                "preferences": request.preferences.model_dump_json(),
                "status": request.status,
                "steps": STEPS.dump_json(request.steps).decode(),
                "plan": request.plan.model_dump_json() if request.plan else None,
                "error": request.error,
                "created_at": to_utc_naive(request.created_at),
                "updated_at": to_utc_naive(request.updated_at),
            },
        )

    def get(self, request_id: str) -> ShoppingRequest | None:
        cursor = self._connection.cursor()
        cursor.execute("select * from shopping_requests where id = ?", [request_id])
        rows = fetch_dicts(cursor)
        return self._to_request(rows[0]) if rows else None

    def recent(self, limit: int) -> list[RequestSummary]:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            select
                id, description, market, budget, status, created_at,
                cast(json_extract(plan, '$.total') as double) as total,
                coalesce(json_array_length(json_extract(plan, '$.items')), 0) as item_count
            from shopping_requests
            order by created_at desc
            limit ?
            """,
            [limit],
        )
        return [
            RequestSummary(
                id=row["id"],
                description=row["description"],
                market=Market.model_validate_json(row["market"]),
                budget=row["budget"],
                status=row["status"],
                total=row["total"],
                item_count=row["item_count"],
                created_at=row["created_at"].replace(tzinfo=UTC),
            )
            for row in fetch_dicts(cursor)
        ]

    def delete(self, request_id: str) -> None:
        self._connection.cursor().execute(
            "delete from shopping_requests where id = ?", [request_id]
        )

    def requeue_unfinished(self) -> list[str]:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            update shopping_requests
            set status = 'queued', steps = '[]', updated_at = ?
            where status in ('queued', 'running')
            returning id, created_at
            """,
            [to_utc_naive(datetime.now(UTC))],
        )
        rows = sorted(fetch_dicts(cursor), key=lambda row: row["created_at"])
        return [row["id"] for row in rows]

    def count_since(self, moment: datetime) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            "select count(*) as total from shopping_requests where created_at >= ?",
            [to_utc_naive(moment)],
        )
        return int(fetch_dicts(cursor)[0]["total"])

    @staticmethod
    def _to_request(row: dict[str, Any]) -> ShoppingRequest:
        plan = row["plan"]
        return ShoppingRequest(
            id=row["id"],
            description=row["description"],
            market=Market.model_validate_json(row["market"]),
            budget=row["budget"],
            preferences=Preferences.model_validate_json(row["preferences"]),
            status=row["status"],
            steps=STEPS.validate_json(row["steps"]),
            plan=ShoppingPlan.model_validate_json(plan) if plan else None,
            error=row["error"],
            created_at=row["created_at"].replace(tzinfo=UTC),
            updated_at=row["updated_at"].replace(tzinfo=UTC),
        )


def to_utc_naive(moment: datetime) -> datetime:
    return moment.astimezone(UTC).replace(tzinfo=None)
