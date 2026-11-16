import contextvars
import logging
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import openai
from openai.types.responses import (
    ParsedResponseFunctionToolCall,
    ResponseInputItemParam,
    ToolParam,
)
from pydantic import BaseModel

from price_scout.application.shopping_request.ports import AgentTools
from price_scout.application.shopping_request.tool_models import (
    CategoryMetricsInput,
    CheckFitInput,
    PlanBudgetInput,
    SearchOffersInput,
)

logger = logging.getLogger(__name__)

MAX_PARALLEL_TOOLS = 4


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    arguments: type[BaseModel]
    run: Callable[[BaseModel], BaseModel]


class OpenAiAgentTools:
    def __init__(self, tools: AgentTools) -> None:
        specs = [
            ToolSpec(
                name="plan_budget",
                description=(
                    "Record how the request's budget is split between the items. Call it "
                    "before searching, and again whenever you change the split."
                ),
                arguments=PlanBudgetInput,
                run=lambda args: tools.plan_budget(_as(args, PlanBudgetInput)),
            ),
            ToolSpec(
                name="search_offers",
                description=(
                    "Search Google Shopping in the request's country, drop listings that do "
                    "not fit, and group the rest into products. Returns the cheapest products "
                    "within the limits, with how many stores sell each and the most "
                    "installments offered. Each call costs a paid search: never repeat a query."
                ),
                arguments=SearchOffersInput,
                run=lambda args: tools.search_offers(_as(args, SearchOffersInput)),
            ),
            ToolSpec(
                name="check_fit",
                description="Check whether a product returned by search_offers fits a space.",
                arguments=CheckFitInput,
                run=lambda args: tools.check_fit(_as(args, CheckFitInput)),
            ),
            ToolSpec(
                name="category_metrics",
                description=(
                    "Average, minimum and maximum price of a category across every search in "
                    "this country. Use it to judge a price or to split the budget."
                ),
                arguments=CategoryMetricsInput,
                run=lambda args: tools.category_metrics(_as(args, CategoryMetricsInput)),
            ),
        ]
        self._specs = {spec.name: spec for spec in specs}

    def definitions(self) -> list[ToolParam]:
        return [
            openai.pydantic_responses_function_tool(
                spec.arguments, name=spec.name, description=spec.description
            )
            for spec in self._specs.values()
        ]

    def answer(self, output: Iterable[object]) -> list[ResponseInputItemParam]:
        calls = [item for item in output if isinstance(item, ParsedResponseFunctionToolCall)]
        return [
            {"type": "function_call_output", "call_id": call.call_id, "output": result}
            for call, result in zip(calls, self._run_all(calls), strict=True)
        ]

    def _run_all(self, calls: list[ParsedResponseFunctionToolCall]) -> list[str]:
        if len(calls) <= 1:
            return [self._run(call) for call in calls]
        contexts = [contextvars.copy_context() for _ in calls]
        with ThreadPoolExecutor(max_workers=min(MAX_PARALLEL_TOOLS, len(calls))) as pool:
            return list(
                pool.map(
                    lambda pair: pair[0].run(self._run, pair[1]), zip(contexts, calls, strict=True)
                )
            )

    def _run(self, call: ParsedResponseFunctionToolCall) -> str:
        spec = self._specs.get(call.name)
        if spec is None:
            return f"error: unknown tool {call.name}"
        try:
            arguments = spec.arguments.model_validate(call.parsed_arguments)
            return spec.run(arguments).model_dump_json()
        except Exception as error:
            logger.info("tool %s failed: %s", call.name, error)
            return f"error: {error}"


def _as[M: BaseModel](arguments: BaseModel, model: type[M]) -> M:
    if not isinstance(arguments, model):
        raise TypeError(f"expected {model.__name__}, got {type(arguments).__name__}")
    return arguments
