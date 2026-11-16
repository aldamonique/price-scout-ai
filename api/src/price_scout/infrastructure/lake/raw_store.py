from pathlib import Path

from price_scout.domain.catalog.models import RawSearch


class FileRawStore:
    def __init__(self, bronze_dir: Path) -> None:
        self._dir = bronze_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, raw: RawSearch) -> None:
        path = self._path(raw.search_id)
        if not path.exists():
            path.write_text(raw.model_dump_json(), encoding="utf-8")

    def load(self, search_id: str) -> RawSearch | None:
        path = self._path(search_id)
        if not path.exists():
            return None
        return RawSearch.model_validate_json(path.read_text(encoding="utf-8"))

    def _path(self, search_id: str) -> Path:
        return self._dir / f"{search_id}.json"
