import re
from pathlib import Path

import duckdb

GOLD_DIR = Path(__file__).resolve().parents[2] / "analytics" / "models" / "gold"
SOURCE = re.compile(r"\{\{\s*source\(\s*'app'\s*,\s*'(\w+)'\s*\)\s*\}\}")
REF = re.compile(r"\{\{\s*ref\(\s*'(\w+)'\s*\)\s*\}\}")


def create_gold_views(connection: duckdb.DuckDBPyConnection, *names: str) -> None:
    for name in names:
        sql = (GOLD_DIR / f"{name}.sql").read_text(encoding="utf-8")
        sql = REF.sub(r"\1", SOURCE.sub(r"\1", sql))
        connection.execute(f"create or replace view {name} as {sql}")
