from typing import Protocol

from price_scout.domain.catalog.models import Offer, SearchIntent
from price_scout.domain.judgment.models import Judgment


class OfferJudge(Protocol):
    @property
    def version(self) -> str: ...

    def judge(self, intent: SearchIntent, offers: list[Offer]) -> Judgment: ...


class JudgmentRepository(Protocol):
    def is_judged(self, search_id: str, version: str) -> bool: ...

    def save(self, search_id: str, judgment: Judgment, version: str) -> None: ...

    def discarded_count(self, search_id: str) -> int: ...
