import hashlib
import re
import unicodedata
from datetime import date

from price_scout.domain.catalog.models import Product


def search_id_for(query: str, country: str, day: date) -> str:
    normalized = " ".join(query.lower().split())
    key = f"{country}:{normalized}:{day.isoformat()}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def _plain(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def preference_matches(name: str, words: list[str]) -> int:
    plain = _plain(name)
    return sum(
        1
        for word in (_plain(word).strip() for word in words)
        if word and re.search(r"\b" + re.escape(word) + r"\b", plain)
    )


def rank_by_preference(products: list[Product], words: list[str]) -> list[Product]:
    return sorted(
        products,
        key=lambda product: (-preference_matches(product.name, words), product.min_price),
    )
