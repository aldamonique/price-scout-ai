from datetime import UTC

import duckdb

from price_scout.domain.observability.models import LlmCall
from price_scout.infrastructure.duckdb.connection import fetch_dicts
from price_scout.infrastructure.duckdb.shopping_request_repository import to_utc_naive


class DuckDbCallLog:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def record(self, call: LlmCall) -> None:
        self._connection.cursor().execute(
            """
            insert into llm_calls (
                id, request_id, task, model, prompt_version, input_tokens, output_tokens,
                cost_usd, latency_ms, ok, error, created_at
            ) values (
                $id, $request_id, $task, $model, $prompt_version, $input_tokens,
                $output_tokens, $cost_usd, $latency_ms, $ok, $error, $created_at
            )
            """,
            {**call.model_dump(), "created_at": to_utc_naive(call.created_at)},
        )

    def delete_for_request(self, request_id: str) -> None:
        self._connection.cursor().execute(
            "delete from llm_calls where request_id = ?", [request_id]
        )

    def calls(self, request_id: str) -> list[LlmCall]:
        cursor = self._connection.cursor()
        cursor.execute(
            "select * from llm_calls where request_id = ? order by created_at, id", [request_id]
        )
        return [
            LlmCall.model_validate({**row, "created_at": row["created_at"].replace(tzinfo=UTC)})
            for row in fetch_dicts(cursor)
        ]
