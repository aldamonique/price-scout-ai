import pytest
from builders import BRAZIL, shopping_request
from fakes import (
    FailingAgent,
    InlineJobRunner,
    InMemoryCallLog,
    InMemoryShoppingRequestRepository,
    ScriptedAgent,
    new_run_request,
)

from price_scout.application.shopping_request.delete_request import DeleteShoppingRequest
from price_scout.application.shopping_request.get_request import GetShoppingRequest
from price_scout.application.shopping_request.list_requests import ListShoppingRequests
from price_scout.application.shopping_request.resume_requests import ResumeShoppingRequests
from price_scout.application.shopping_request.submit_request import SubmitShoppingRequest
from price_scout.domain.errors import (
    RateLimitedError,
    RequestInProgressError,
    RequestNotFoundError,
)
from price_scout.domain.observability.models import LlmCall
from price_scout.domain.shopping_request.models import Preferences


def test_submit_returns_a_queued_request_and_runs_it_in_the_background() -> None:
    requests = InMemoryShoppingRequestRepository()
    submit = SubmitShoppingRequest(
        requests, InlineJobRunner(), new_run_request(ScriptedAgent(), requests)
    )

    submitted = submit.execute("furnish the living room", BRAZIL, 3000, Preferences(colors="gray"))

    assert submitted.status == "queued"
    assert submitted.preferences.colors == "gray"
    assert requests.requests[submitted.id].status == "done"


def test_a_finished_request_has_the_plan_steps_and_stats() -> None:
    requests = InMemoryShoppingRequestRepository()
    requests.save(shopping_request())

    new_run_request(ScriptedAgent(), requests).execute("r1")

    finished = requests.requests["r1"]
    assert finished.plan is not None
    assert [item.product.id for item in finished.plan.items] == ["abc-p1"]
    assert (finished.plan.budget, finished.plan.stats.searches) == (3000, 1)
    assert [step.kind for step in finished.steps] == ["plan", "search", "measure"]


def test_progress_is_saved_while_the_agent_works() -> None:
    requests = InMemoryShoppingRequestRepository()
    requests.save(shopping_request())

    new_run_request(ScriptedAgent(), requests).execute("r1")

    step_counts = [len(r.steps) for r in requests.history if r.status == "running"]
    assert step_counts == [0, 1, 2, 3]


def test_an_upstream_failure_fails_the_request_with_its_message() -> None:
    requests = InMemoryShoppingRequestRepository()
    requests.save(shopping_request())

    new_run_request(FailingAgent(), requests).execute("r1")

    failed = requests.requests["r1"]
    assert (failed.status, failed.error) == ("failed", "SerpApi failed: ConnectTimeout")


def test_get_raises_for_an_unknown_request() -> None:
    with pytest.raises(RequestNotFoundError):
        GetShoppingRequest(InMemoryShoppingRequestRepository()).execute("nope")


def test_the_history_limit_is_kept_within_bounds() -> None:
    requests = InMemoryShoppingRequestRepository()
    for number in range(3):
        requests.save(shopping_request(f"r{number}"))
    history = ListShoppingRequests(requests)

    assert len(history.execute(limit=0)) == 1
    assert len(history.execute(limit=2)) == 2


def test_deleting_a_request_also_deletes_its_model_calls() -> None:
    requests, calls = InMemoryShoppingRequestRepository(), InMemoryCallLog()
    requests.save(shopping_request().model_copy(update={"status": "done"}))
    for call_id, request_id in [("c1", "r1"), ("c2", "r2")]:
        calls.record(
            LlmCall(
                id=call_id,
                request_id=request_id,
                task="agent",
                model="m",
                prompt_version="v4",
                input_tokens=1,
                output_tokens=1,
                cost_usd=None,
                latency_ms=1,
                ok=True,
                error=None,
                created_at=shopping_request().created_at,
            )
        )

    DeleteShoppingRequest(requests, calls).execute("r1")

    assert requests.get("r1") is None
    assert [call.id for call in calls.recorded] == ["c2"]


def test_a_running_request_cannot_be_deleted() -> None:
    requests = InMemoryShoppingRequestRepository()
    requests.save(shopping_request().model_copy(update={"status": "running"}))

    with pytest.raises(RequestInProgressError):
        DeleteShoppingRequest(requests, InMemoryCallLog()).execute("r1")

    assert requests.get("r1") is not None


def test_deleting_an_unknown_request_raises() -> None:
    with pytest.raises(RequestNotFoundError):
        DeleteShoppingRequest(InMemoryShoppingRequestRepository(), InMemoryCallLog()).execute("x")


def test_a_request_without_budget_runs_to_a_plan() -> None:
    requests = InMemoryShoppingRequestRepository()
    requests.save(shopping_request(budget=None))

    new_run_request(ScriptedAgent(), requests).execute("r1")

    plan = requests.requests["r1"].plan
    assert plan is not None
    assert (plan.budget, plan.leftover) == (None, None)
    assert plan.insights[0] == "No budget was set; the plan totals R$ 1,299.00."


def test_requests_left_unfinished_by_a_restart_run_again() -> None:
    requests = InMemoryShoppingRequestRepository()
    requests.save(shopping_request("r1").model_copy(update={"status": "running"}))
    requests.save(shopping_request("r2").model_copy(update={"status": "done"}))

    resumed = ResumeShoppingRequests(
        requests, InlineJobRunner(), new_run_request(ScriptedAgent(), requests)
    ).execute()

    assert resumed == 1
    assert requests.requests["r1"].status == "done"


def test_the_demo_limit_refuses_requests_over_the_hourly_cap() -> None:
    requests = InMemoryShoppingRequestRepository()
    now = shopping_request().created_at
    submit = SubmitShoppingRequest(
        requests,
        InlineJobRunner(),
        new_run_request(ScriptedAgent(), requests),
        max_per_hour=2,
        now=lambda: now,
    )

    submit.execute("a sofa for the living room", BRAZIL, None, Preferences())
    submit.execute("a desk for the home office", BRAZIL, None, Preferences())

    with pytest.raises(RateLimitedError):
        submit.execute("a bed for the guest room", BRAZIL, None, Preferences())
