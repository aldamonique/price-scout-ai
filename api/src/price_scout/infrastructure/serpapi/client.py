from datetime import UTC, datetime
from typing import Any

import httpx

from price_scout.domain.catalog.models import RawSearch, SearchIntent
from price_scout.domain.catalog.rules import search_id_for
from price_scout.domain.errors import UpstreamError

SERPAPI_URL = "https://serpapi.com/search.json"


class SerpApiOfferSource:
    def __init__(self, api_key: str, http: httpx.Client) -> None:
        self._api_key = api_key
        self._http = http

    def fetch(self, intent: SearchIntent) -> RawSearch:
        params = {
            "engine": "google_shopping",
            "q": intent.query,
            "gl": intent.market.country,
            "hl": intent.market.language,
            "api_key": self._api_key,
        }
        payload = self._get(params)
        if "shopping_results" not in payload:
            payload = self._get({**params, "no_cache": "true"})

        fetched_at = datetime.now(UTC)
        if "shopping_results" not in payload:
            reason = payload.get("error", "response without shopping_results")
            raise UpstreamError(f'SerpApi returned no listings for "{intent.query}": {reason}')

        return RawSearch(
            search_id=search_id_for(intent.query, intent.market.country, fetched_at.date()),
            query=intent.query,
            country=intent.market.country,
            fetched_at=fetched_at,
            payload=payload,
        )

    def _get(self, params: dict[str, str]) -> dict[str, Any]:
        try:
            response = self._http.get(SERPAPI_URL, params=params, timeout=30)
        except httpx.HTTPError as error:
            raise UpstreamError(f"SerpApi failed: {type(error).__name__}") from None

        if response.is_error:
            raise UpstreamError(f"SerpApi failed ({response.status_code}): {_reason(response)}")

        try:
            payload = response.json()
        except ValueError:
            raise UpstreamError("SerpApi returned a response that is not JSON") from None
        if not isinstance(payload, dict):
            raise UpstreamError("SerpApi returned a response that is not an object")
        return payload


def _reason(response: httpx.Response) -> str:
    try:
        message = response.json().get("error")
    except ValueError:
        message = None
    return message if isinstance(message, str) else response.reason_phrase
