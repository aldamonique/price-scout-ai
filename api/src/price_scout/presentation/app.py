from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from price_scout.application.observability.get_eval_runs import GetEvalRuns
from price_scout.application.observability.get_overview import GetObservability
from price_scout.application.observability.get_request_calls import GetRequestCalls
from price_scout.application.shopping_request.delete_request import DeleteShoppingRequest
from price_scout.application.shopping_request.get_request import GetShoppingRequest
from price_scout.application.shopping_request.list_requests import ListShoppingRequests
from price_scout.application.shopping_request.submit_request import SubmitShoppingRequest
from price_scout.domain.errors import (
    ObservabilityUnavailableError,
    RateLimitedError,
    RequestInProgressError,
    RequestNotFoundError,
)
from price_scout.presentation.routes import health, markets
from price_scout.presentation.routes.observability import build_observability_router
from price_scout.presentation.routes.shopping_requests import build_shopping_requests_router
from price_scout.presentation.security import admin_only


@dataclass(frozen=True)
class UseCases:
    submit_request: SubmitShoppingRequest
    get_request: GetShoppingRequest
    list_requests: ListShoppingRequests
    get_observability: GetObservability
    get_request_calls: GetRequestCalls
    delete_request: DeleteShoppingRequest
    get_eval_runs: GetEvalRuns


def create_app(
    use_cases: UseCases,
    on_shutdown: Callable[[], None] = lambda: None,
    admin_token: str | None = None,
) -> FastAPI:
    admin = admin_only(admin_token)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        on_shutdown()

    app = FastAPI(
        title="Price Scout",
        description="Furniture shopping agent: plans, searches, compares and builds a plan.",
        lifespan=lifespan,
    )

    @app.exception_handler(RequestNotFoundError)
    def request_not_found(_: Request, error: RequestNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": f"No shopping request {error}."},
        )

    @app.exception_handler(RequestInProgressError)
    def request_in_progress(_: Request, error: RequestInProgressError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "This request is still running. Wait for it to finish."},
        )

    @app.exception_handler(RateLimitedError)
    def rate_limited(_: Request, error: RateLimitedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": f"The demo accepts {error} requests per hour. Try again later."},
            headers={"Retry-After": "600"},
        )

    @app.exception_handler(ObservabilityUnavailableError)
    def observability_unavailable(_: Request, error: ObservabilityUnavailableError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"detail": str(error)}
        )

    app.include_router(health.router)
    app.include_router(markets.router)
    app.include_router(
        build_shopping_requests_router(
            use_cases.submit_request,
            use_cases.get_request,
            use_cases.list_requests,
            use_cases.delete_request,
            admin,
        )
    )
    app.include_router(
        build_observability_router(
            use_cases.get_observability,
            use_cases.get_request_calls,
            use_cases.get_eval_runs,
            admin,
        )
    )
    return app
