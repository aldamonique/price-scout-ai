import json
from pathlib import Path

from pydantic import BaseModel

from price_scout.domain.catalog.models import Category

CASES_DIR = Path(__file__).parent / "cases"


class Listing(BaseModel):
    id: str
    title: str
    store: str
    price: float | None


class Expected(BaseModel):
    groups: list[list[str]]
    discard: list[str]


class Case(BaseModel):
    id: str
    source: str
    note: str
    query: str
    category: Category
    country: str
    listings: list[Listing]
    expected: Expected


def load_cases(directory: Path = CASES_DIR) -> list[Case]:
    return [
        Case.model_validate(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(directory.glob("*.json"))
    ]
