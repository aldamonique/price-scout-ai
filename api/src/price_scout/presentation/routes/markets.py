from fastapi import APIRouter

from price_scout.domain.catalog.markets import MARKETS
from price_scout.domain.catalog.models import Market

router = APIRouter(tags=["markets"])


@router.get("/markets", summary="The countries the app can shop in")
def list_markets() -> list[Market]:
    return list(MARKETS.values())
