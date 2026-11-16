from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from price_scout.application.shopping_request.delete_request import DeleteShoppingRequest
from price_scout.application.shopping_request.get_request import GetShoppingRequest
from price_scout.application.shopping_request.list_requests import ListShoppingRequests
from price_scout.application.shopping_request.submit_request import SubmitShoppingRequest
from price_scout.domain.catalog.markets import MARKETS
from price_scout.domain.shopping_request.models import (
    Preferences,
    RequestSummary,
    ShoppingRequest,
)


class ShoppingRequestBody(BaseModel):
    description: str = Field(
        min_length=10, max_length=600, description="What the user needs, in free text."
    )
    country: str = Field(description='A country code from GET /markets, e.g. "br".')
    budget: float | None = Field(
        default=None, gt=0, le=10_000_000, description="In the country's currency. Optional."
    )
    preferences: Preferences = Preferences()


def build_shopping_requests_router(
    submit_request: SubmitShoppingRequest,
    get_request: GetShoppingRequest,
    list_requests: ListShoppingRequests,
    delete_request: DeleteShoppingRequest,
    admin: Callable[..., None],
) -> APIRouter:
    router = APIRouter(prefix="/shopping-requests", tags=["shopping requests"])

    @router.post(
        "",
        status_code=status.HTTP_202_ACCEPTED,
        summary="Submit a shopping request",
        description="Returns at once with the request id. Poll GET /shopping-requests/{id}.",
        responses={
            422: {"description": "Invalid fields or a country the app does not cover."},
            429: {"description": "Too many requests in the last hour."},
        },
    )
    def submit(body: ShoppingRequestBody, response: Response) -> ShoppingRequest:
        market = MARKETS.get(body.country.lower())
        if market is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Country {body.country!r} is not covered. See GET /markets.",
            )
        request = submit_request.execute(body.description, market, body.budget, body.preferences)
        response.headers["Location"] = f"/shopping-requests/{request.id}"
        return request

    @router.get("", summary="List shopping requests, newest first")
    def history(limit: int = Query(default=50, ge=1, le=200)) -> list[RequestSummary]:
        return list_requests.execute(limit)

    @router.get(
        "/{request_id}",
        summary="Read a shopping request and its progress",
        responses={404: {"description": "No shopping request with this id."}},
    )
    def read(request_id: str) -> ShoppingRequest:
        return get_request.execute(request_id)

    @router.delete(
        "/{request_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Depends(admin)],
        summary="Delete a finished shopping request and its model calls",
        responses={
            404: {"description": "No shopping request with this id."},
            401: {"description": "The admin token is missing or wrong."},
            409: {"description": "The request is still running."},
        },
    )
    def delete(request_id: str) -> None:
        delete_request.execute(request_id)

    return router
