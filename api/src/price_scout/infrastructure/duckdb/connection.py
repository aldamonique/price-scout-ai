from pathlib import Path
from typing import Any

import duckdb

from price_scout.config import LakeSettings

SCHEMA_FILE = Path(__file__).parent / "schema.sql"


def open_warehouse(data_dir: Path, lake: LakeSettings | None = None) -> duckdb.DuckDBPyConnection:
    data_dir.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(data_dir / "warehouse.duckdb"))
    connection.execute(f"set global file_search_path = '{data_dir.as_posix()}'")
    if lake is not None and lake.backend == "s3":
        connect_lake(connection, lake)
    connection.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
    return connection


def connect_lake(connection: duckdb.DuckDBPyConnection, lake: LakeSettings) -> None:
    connection.execute("install httpfs")
    connection.execute("load httpfs")
    options: dict[str, str | bool] = {
        "TYPE": "s3",
        "KEY_ID": lake.access_key_id or "",
        "SECRET": lake.secret_access_key or "",
        "REGION": lake.region,
        "USE_SSL": lake.use_ssl,
    }
    if lake.endpoint:
        options |= {"ENDPOINT": lake.endpoint, "URL_STYLE": "path"}
    body = ", ".join(f"{key} {_literal(value)}" for key, value in options.items())
    connection.execute(f"create or replace secret lake ({body})")


def _literal(value: str | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return "'" + value.replace("'", "''") + "'"


def fetch_dicts(cursor: duckdb.DuckDBPyConnection) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description or []]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def fetch_one(cursor: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    rows = fetch_dicts(cursor)
    if len(rows) != 1:
        raise LookupError(f"expected one row, got {len(rows)}")
    return rows[0]
