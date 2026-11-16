import hashlib
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field

from price_scout.domain.catalog.models import Offer


def _tokens(name: str) -> tuple[str, ...]:
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return tuple(token for token in re.split(r"[^a-z0-9]+", plain) if token)


@dataclass(frozen=True)
class StorePolicy:
    blocked: tuple[str, ...] = ()
    reason: str = "store not allowed"

    def blocks(self, store: str) -> bool:
        tokens = _tokens(store)
        return any(
            pattern and tokens[: len(pattern)] == pattern for pattern in map(_tokens, self.blocked)
        )

    def split(self, offers: list[Offer]) -> tuple[list[Offer], list[Offer]]:
        allowed = [offer for offer in offers if not self.blocks(offer.store)]
        blocked = [offer for offer in offers if self.blocks(offer.store)]
        return allowed, blocked

    @property
    def version(self) -> str:
        names = "\n".join(sorted(" ".join(_tokens(name)) for name in self.blocked))
        return "stores-" + hashlib.sha256(names.encode()).hexdigest()[:8]


@dataclass(frozen=True)
class StorePolicies:
    default: StorePolicy = StorePolicy()
    by_country: Mapping[str, StorePolicy] = field(default_factory=dict)

    def for_country(self, country: str) -> StorePolicy:
        return self.by_country.get(country.lower(), self.default)
