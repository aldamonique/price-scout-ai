from price_scout.domain.catalog.models import RawSearch
from price_scout.domain.catalog.ports import RawStore


class MirroredRawStore:
    def __init__(self, primary: RawStore, mirror: RawStore) -> None:
        self._primary = primary
        self._mirror = mirror

    def save(self, raw: RawSearch) -> None:
        self._primary.save(raw)
        self._mirror.save(raw)

    def load(self, search_id: str) -> RawSearch | None:
        raw = self._primary.load(search_id)
        if raw is not None:
            return raw
        raw = self._mirror.load(search_id)
        if raw is not None:
            self._primary.save(raw)
        return raw
