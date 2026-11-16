import re
from pathlib import Path

MACRO = re.compile(
    r"\{%-?\s*macro\s+silver_offers_from\(bronze\)\s*-?%\}(?P<body>.*?)\{%-?\s*endmacro\s*-?%\}",
    re.DOTALL,
)
BRONZE = re.compile(r"\{\{\s*bronze\s*\}\}")
SOURCE = re.compile(r"\{\{\s*source\(\s*'app'\s*,\s*'(\w+)'\s*\)\s*\}\}")
REF = re.compile(r"\{\{\s*ref\(\s*'(\w+)'\s*\)\s*\}\}")
GOLD_MODELS = ("gold_product_offers", "gold_products")


class MedallionSql:
    def __init__(self, analytics_dir: Path) -> None:
        macro = (analytics_dir / "macros" / "silver_offers.sql").read_text(encoding="utf-8")
        match = MACRO.search(macro)
        if match is None:
            raise ValueError("analytics/macros/silver_offers.sql has no silver_offers_from macro")
        self._silver = match["body"]
        self._gold = {
            name: _render(
                (analytics_dir / "models" / "gold" / f"{name}.sql").read_text(encoding="utf-8")
            )
            for name in GOLD_MODELS
        }

    def for_search(self, bronze_file: str) -> str:
        literal = bronze_file.replace("\\", "/").replace("'", "''")
        silver = BRONZE.sub(lambda _: literal, self._silver)
        _ensure_rendered(silver)
        gold = ",\n".join(f"{name} as ({sql})" for name, sql in self._gold.items())
        return (
            "with\n"
            f"silver_offers as ({silver}),\n"
            "app_judged_offers as (select * from judged_offers where search_id = $search_id),\n"
            f"{gold}\n"
        )


def _render(sql: str) -> str:
    rendered = REF.sub(r"\1", SOURCE.sub(r"app_\1", sql))
    _ensure_rendered(rendered)
    return rendered


def _ensure_rendered(sql: str) -> None:
    if "{{" in sql or "{%" in sql:
        raise ValueError("dbt SQL still has Jinja the API cannot render")
