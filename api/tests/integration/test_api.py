from pathlib import Path

import pytest
from fakes import (
    FakeObservabilityReader,
    InlineJobRunner,
    InMemoryCallLog,
    InMemoryShoppingRequestRepository,
    ScriptedAgent,
    new_run_request,
)
from fastapi.testclient import TestClient

from price_scout.application.observability.get_eval_runs import GetEvalRuns
from price_scout.application.observability.get_overview import GetObservability
from price_scout.application.observability.get_request_calls import GetRequestCalls
from price_scout.application.shopping_request.delete_request import DeleteShoppingRequest
from price_scout.application.shopping_request.get_request import GetShoppingRequest
from price_scout.application.shopping_request.list_requests import ListShoppingRequests
from price_scout.application.shopping_request.submit_request import SubmitShoppingRequest
from price_scout.infrastructure.evals.json_results import JsonEvalResults
from price_scout.presentation.app import UseCases, create_app

BODY = {
    "description": "furnish the living room",
    "country": "br",
    "budget": 3000,
    "preferences": {
        "brands": None,
        "colors": "gray",
        "materials": None,
        "payment": None,
        "notes": None,
    },
}


@pytest.fixture
def client() -> TestClient:
    requests = InMemoryShoppingRequestRepository()
    calls = InMemoryCallLog()
    app = create_app(
        UseCases(
            submit_request=SubmitShoppingRequest(
                requests, InlineJobRunner(), new_run_request(ScriptedAgent(), requests)
            ),
            get_request=GetShoppingRequest(requests),
            list_requests=ListShoppingRequests(requests),
            get_observability=GetObservability(FakeObservabilityReader()),
            get_request_calls=GetRequestCalls(requests, calls),
            delete_request=DeleteShoppingRequest(requests, calls),
            get_eval_runs=GetEvalRuns(JsonEvalResults(Path("missing"))),
        )
    )
    return TestClient(app)


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_the_markets_list_the_countries_covered(client: TestClient) -> None:
    countries = {market["country"] for market in client.get("/markets").json()}

    assert {"br", "us", "pt"} <= countries


def test_submitting_a_request_answers_at_once_with_its_location(client: TestClient) -> None:
    response = client.post("/shopping-requests", json=BODY)

    assert response.status_code == 202
    body = response.json()
    assert (body["status"], body["market"]["currency"]) == ("queued", "BRL")
    assert body["preferences"]["colors"] == "gray"
    assert response.headers["location"] == f"/shopping-requests/{body['id']}"


def test_the_request_can_be_read_with_its_plan_and_steps(client: TestClient) -> None:
    request_id = client.post("/shopping-requests", json=BODY).json()["id"]

    body = client.get(f"/shopping-requests/{request_id}").json()

    assert body["status"] == "done"
    assert body["plan"]["items"][0]["product"]["id"] == "abc-p1"
    assert [step["kind"] for step in body["steps"]] == ["plan", "search", "measure"]


def test_the_history_lists_requests_with_their_totals(client: TestClient) -> None:
    request_id = client.post("/shopping-requests", json=BODY).json()["id"]

    history = client.get("/shopping-requests").json()

    assert [(r["id"], r["status"], r["item_count"]) for r in history] == [(request_id, "done", 1)]
    assert history[0]["total"] == 1299


def test_the_history_limit_is_bounded(client: TestClient) -> None:
    assert client.get("/shopping-requests?limit=0").status_code == 422


def test_preferences_are_optional(client: TestClient) -> None:
    body = {k: v for k, v in BODY.items() if k != "preferences"}

    assert client.post("/shopping-requests", json=body).status_code == 202


def test_an_unknown_request_is_404(client: TestClient) -> None:
    assert client.get("/shopping-requests/nope").status_code == 404


@pytest.mark.parametrize(
    "change",
    [{"description": "hi"}, {"country": "zz"}, {"budget": 0}],
)
def test_invalid_fields_are_rejected(client: TestClient, change: dict[str, object]) -> None:
    assert client.post("/shopping-requests", json={**BODY, **change}).status_code == 422


def test_the_observability_overview_is_served(client: TestClient) -> None:
    body = client.get("/observability").json()

    assert body["runs"]["requests"] == 0
    assert body["llm"]["error_rate"] is None


def test_the_calls_of_a_request_are_listed(client: TestClient) -> None:
    request_id = client.post("/shopping-requests", json=BODY).json()["id"]

    response = client.get(f"/observability/requests/{request_id}/calls")

    assert (response.status_code, response.json()) == (200, [])


def test_the_calls_of_an_unknown_request_are_404(client: TestClient) -> None:
    assert client.get("/observability/requests/nope/calls").status_code == 404


def test_the_budget_is_optional(client: TestClient) -> None:
    body = {k: v for k, v in BODY.items() if k != "budget"}

    response = client.post("/shopping-requests", json=body)

    assert response.status_code == 202
    assert response.json()["budget"] is None
    plan = client.get(response.headers["location"]).json()["plan"]
    assert (plan["budget"], plan["leftover"]) == (None, None)


def test_a_finished_request_can_be_deleted(client: TestClient) -> None:
    request_id = client.post("/shopping-requests", json=BODY).json()["id"]

    assert client.delete(f"/shopping-requests/{request_id}").status_code == 204
    assert client.get(f"/shopping-requests/{request_id}").status_code == 404
    assert client.get("/shopping-requests").json() == []


def test_deleting_an_unknown_request_is_404(client: TestClient) -> None:
    assert client.delete("/shopping-requests/nope").status_code == 404


def admin_client(token: str = "secret") -> TestClient:
    requests = InMemoryShoppingRequestRepository()
    calls = InMemoryCallLog()
    app = create_app(
        UseCases(
            submit_request=SubmitShoppingRequest(
                requests, InlineJobRunner(), new_run_request(ScriptedAgent(), requests)
            ),
            get_request=GetShoppingRequest(requests),
            list_requests=ListShoppingRequests(requests),
            get_observability=GetObservability(FakeObservabilityReader()),
            get_request_calls=GetRequestCalls(requests, calls),
            delete_request=DeleteShoppingRequest(requests, calls),
            get_eval_runs=GetEvalRuns(JsonEvalResults(Path("missing"))),
        ),
        admin_token=token,
    )
    return TestClient(app)


def test_with_an_admin_token_observability_and_delete_need_it() -> None:
    client = admin_client()
    request_id = client.post("/shopping-requests", json=BODY).json()["id"]

    assert client.get("/observability").status_code == 401
    assert client.delete(f"/shopping-requests/{request_id}").status_code == 401
    assert (
        client.get("/observability", headers={"Authorization": "Bearer wrong"}).status_code == 401
    )

    auth = {"Authorization": "Bearer secret"}
    assert client.get("/observability", headers=auth).status_code == 200
    assert client.delete(f"/shopping-requests/{request_id}", headers=auth).status_code == 204


def test_with_an_admin_token_shopping_stays_open() -> None:
    client = admin_client()

    assert client.post("/shopping-requests", json=BODY).status_code == 202
    assert client.get("/shopping-requests").status_code == 200
    assert client.get("/markets").status_code == 200


def test_over_the_hourly_cap_the_api_answers_429() -> None:
    requests = InMemoryShoppingRequestRepository()
    calls = InMemoryCallLog()
    client = TestClient(
        create_app(
            UseCases(
                submit_request=SubmitShoppingRequest(
                    requests,
                    InlineJobRunner(),
                    new_run_request(ScriptedAgent(), requests),
                    max_per_hour=0,
                ),
                get_request=GetShoppingRequest(requests),
                list_requests=ListShoppingRequests(requests),
                get_observability=GetObservability(FakeObservabilityReader()),
                get_request_calls=GetRequestCalls(requests, calls),
                delete_request=DeleteShoppingRequest(requests, calls),
                get_eval_runs=GetEvalRuns(JsonEvalResults(Path("missing"))),
            )
        )
    )

    response = client.post("/shopping-requests", json=BODY)

    assert response.status_code == 429
    assert response.headers["retry-after"] == "600"


def test_the_eval_runs_are_listed(client: TestClient) -> None:
    assert client.get("/observability/evals").json() == []
