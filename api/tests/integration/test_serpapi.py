import httpx
import pytest

from price_scout.domain.catalog.models import Market, SearchIntent
from price_scout.domain.errors import UpstreamError
from price_scout.infrastructure.serpapi.client import SerpApiOfferSource

PORTUGAL = Market(country="pt", language="pt-pt", currency="EUR")
INTENT = SearchIntent(query="sofá 3 lugares", category="furniture", market=PORTUGAL)


def source(handler: httpx.MockTransport) -> SerpApiOfferSource:
    return SerpApiOfferSource("secret-key", httpx.Client(transport=handler))


def test_searches_google_shopping_in_the_intent_market() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"shopping_results": [{"title": "Sofá"}]})

    raw = source(httpx.MockTransport(handler)).fetch(INTENT)

    params = requests[0].url.params
    assert (params["engine"], params["gl"], params["hl"], params["q"]) == (
        "google_shopping",
        "pt",
        "pt-pt",
        "sofá 3 lugares",
    )
    assert raw.country == "pt"
    assert raw.payload["shopping_results"] == [{"title": "Sofá"}]


def test_an_http_error_never_leaks_the_api_key() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(500))

    with pytest.raises(UpstreamError) as error:
        source(transport).fetch(INTENT)

    assert "secret-key" not in str(error.value)


def test_an_http_error_explains_why_with_serpapi_message() -> None:
    body = {
        "error": "Invalid API key. Your API key should be here: https://serpapi.com/manage-api-key"
    }
    transport = httpx.MockTransport(lambda _: httpx.Response(401, json=body))

    with pytest.raises(UpstreamError, match=r"SerpApi failed \(401\): Invalid API key"):
        source(transport).fetch(INTENT)


def test_a_network_failure_never_leaks_the_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot reach {request.url}", request=request)

    with pytest.raises(UpstreamError) as error:
        source(httpx.MockTransport(handler)).fetch(INTENT)

    assert str(error.value) == "SerpApi failed: ConnectError"


def test_a_response_without_listings_is_an_error_after_one_uncached_retry() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"error": "No results"})

    with pytest.raises(UpstreamError, match='no listings for "sofá 3 lugares": No results'):
        source(httpx.MockTransport(handler)).fetch(INTENT)

    assert [request.url.params.get("no_cache") for request in requests] == [None, "true"]


def test_an_empty_answer_is_retried_without_serpapi_cache() -> None:
    answers = iter([{"error": "No results"}, {"shopping_results": [{"title": "Teclado mecânico"}]}])
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=next(answers)))

    raw = source(transport).fetch(INTENT)

    assert raw.payload["shopping_results"] == [{"title": "Teclado mecânico"}]
