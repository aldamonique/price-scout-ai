from collections.abc import Callable

from fastapi import APIRouter, Depends

from price_scout.application.observability.get_eval_runs import GetEvalRuns
from price_scout.application.observability.get_overview import GetObservability
from price_scout.application.observability.get_request_calls import GetRequestCalls
from price_scout.domain.observability.models import EvalRun, LlmCall, Overview


def build_observability_router(
    get_overview: GetObservability,
    get_request_calls: GetRequestCalls,
    get_eval_runs: GetEvalRuns,
    admin: Callable[..., None],
) -> APIRouter:
    router = APIRouter(
        prefix="/observability",
        tags=["observability"],
        dependencies=[Depends(admin)],
        responses={401: {"description": "The admin token is missing or wrong."}},
    )

    @router.get(
        "",
        summary="Agent runs, model calls, tools and costs",
        responses={503: {"description": "The dbt views are missing; run dbt build."}},
    )
    def overview() -> Overview:
        return get_overview.execute()

    @router.get(
        "/requests/{request_id}/calls",
        summary="Every model call of one shopping request, in order",
        responses={404: {"description": "No shopping request with this id."}},
    )
    def request_calls(request_id: str) -> list[LlmCall]:
        return get_request_calls.execute(request_id)

    @router.get("/evals", summary="Judge accuracy runs on the labeled cases, newest first")
    def eval_runs() -> list[EvalRun]:
        return get_eval_runs.execute()

    return router
