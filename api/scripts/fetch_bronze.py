import sys

import httpx

from price_scout.bootstrap import new_raw_store
from price_scout.config import Settings
from price_scout.domain.catalog.models import Market, SearchIntent
from price_scout.infrastructure.lake.cached_source import CachedOfferSource
from price_scout.infrastructure.serpapi.client import SerpApiOfferSource

DEFAULT_MARKET = ("br", "pt-br", "BRL")


def main() -> None:
    query, *market_args = sys.argv[1:5]
    country, language, currency = (*market_args, *DEFAULT_MARKET[len(market_args) :])
    market = Market(country=country, language=language, currency=currency)
    settings = Settings()
    store = new_raw_store(settings)
    with httpx.Client() as http:
        source = CachedOfferSource(SerpApiOfferSource(settings.serpapi_key, http), store)
        raw = source.fetch(SearchIntent(query=query, category="other", market=market))
    store.save(raw)

    count = len(raw.payload["shopping_results"])
    print(f"{count} listings in bronze ({settings.lake.backend}): {raw.search_id}.json")


if __name__ == "__main__":
    main()
