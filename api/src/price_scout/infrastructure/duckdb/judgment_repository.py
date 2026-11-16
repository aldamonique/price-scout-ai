import duckdb

from price_scout.domain.judgment.models import Judgment
from price_scout.infrastructure.duckdb.connection import fetch_one

INSERT_JUDGED_OFFER = """
insert into judged_offers (
    search_id, offer_id, product_key, product_name, category,
    width_cm, depth_cm, height_cm, discarded, discard_reason, judge_version
) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


class DuckDbJudgmentRepository:
    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def is_judged(self, search_id: str, version: str) -> bool:
        cursor = self._connection.cursor()
        cursor.execute(
            "select count(*) as total from judged_offers where search_id = ? and judge_version = ?",
            [search_id, version],
        )
        return int(fetch_one(cursor)["total"]) > 0

    def discarded_count(self, search_id: str) -> int:
        return self._count(search_id, only_discarded=True)

    def save(self, search_id: str, judgment: Judgment, version: str) -> None:
        rows: list[tuple[object, ...]] = [
            (
                search_id,
                offer_id,
                f"p{number}",
                group.name,
                group.category,
                group.width_cm,
                group.depth_cm,
                group.height_cm,
                False,
                None,
                version,
            )
            for number, group in enumerate(judgment.products, start=1)
            for offer_id in group.offer_ids
        ]
        rows += [
            (
                search_id,
                item.offer_id,
                None,
                None,
                None,
                None,
                None,
                None,
                True,
                item.reason,
                version,
            )
            for item in judgment.discarded
        ]

        cursor = self._connection.cursor()
        cursor.execute("begin")
        try:
            cursor.execute("delete from judged_offers where search_id = ?", [search_id])
            if rows:
                cursor.executemany(INSERT_JUDGED_OFFER, rows)
            cursor.execute("commit")
        except Exception:
            cursor.execute("rollback")
            raise

    def _count(self, search_id: str, only_discarded: bool) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            """
            select count(*) as total from judged_offers
            where search_id = ? and (not ? or discarded)
            """,
            [search_id, only_discarded],
        )
        return int(fetch_one(cursor)["total"])
