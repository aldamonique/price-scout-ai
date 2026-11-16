import sys
from datetime import UTC, datetime
from pathlib import Path

from price_scout.bootstrap import new_raw_store
from price_scout.config import Settings
from price_scout.domain.catalog.models import RawSearch

PLACEHOLDER = RawSearch(
    search_id="_placeholder",
    query="",
    country="",
    fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
    payload={"shopping_results": []},
)


def main(source: Path) -> None:
    settings = Settings()
    if settings.lake.backend != "s3":
        raise SystemExit("Set LAKE__BACKEND=s3 first.")
    lake = new_raw_store(settings)
    lake.save(PLACEHOLDER)
    files = sorted(source.glob("*.json"))
    for path in files:
        lake.save(RawSearch.model_validate_json(path.read_text(encoding="utf-8")))
        print(f"synced {path.name}")
    print(f"{len(files)} searches synced to s3://{settings.lake.bucket}/bronze/")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Settings().data_dir / "bronze")
