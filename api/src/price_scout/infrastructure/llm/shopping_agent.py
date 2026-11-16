from datetime import date

import openai
from openai.types.responses import ResponseInputItemParam
from openai.types.shared_params import Reasoning

from price_scout.application.shopping_request.ports import AgentTools
from price_scout.domain.errors import UpstreamError
from price_scout.domain.formatting import money
from price_scout.domain.shopping_request.models import AgentPlan, AgentUsage, ShoppingRequest
from price_scout.infrastructure.llm.agent_tools import OpenAiAgentTools
from price_scout.infrastructure.llm.prompts import load_prompt
from price_scout.infrastructure.llm.tracing import CallTracer, NullCallLog, tracing
from price_scout.infrastructure.llm.usage import ModelPricing, UsageMeter


def request_message(request: ShoppingRequest, today: date) -> str:
    market = request.market
    facts = [
        f"Country: {market.country} (store language: {market.language})",
        (
            f"Budget: {money(request.budget, market.currency)} ({market.currency})"
            if request.budget is not None
            else f"Budget: not set (prices in {market.currency})"
        ),
        *request.preferences.as_lines(),
    ]
    return (
        f"Today is {today:%Y-%m-%d}.\n\n"
        f"<request>\n{request.description}\n</request>\n\n"
        "<facts>\n" + "\n".join(facts) + "\n</facts>"
    )


class OpenAiShoppingAgent:
    def __init__(
        self,
        client: openai.OpenAI,
        model: str,
        reasoning: Reasoning | None,
        business_context: str,
        pricing: ModelPricing | None,
        prompt_version: str,
        max_turns: int = 20,
        tracer: CallTracer | None = None,
    ) -> None:
        self._tracer = tracer or CallTracer(NullCallLog())
        self._client = client
        self._model = model
        self._reasoning = reasoning
        self._pricing = pricing
        self._max_turns = max_turns
        self._prompt_version = prompt_version
        self._instructions = (
            load_prompt("agent", prompt_version)
            + f"\n\n<business_context>\n{business_context}\n</business_context>"
        )

    def run(self, request: ShoppingRequest, tools: AgentTools) -> tuple[AgentPlan, AgentUsage]:
        with tracing(request.id, UsageMeter()) as meter:
            plan = self._loop(request_message(request, date.today()), OpenAiAgentTools(tools))
            usage = meter.usage().model_copy(
                update={"agent_model": self._model, "agent_prompt_version": self._prompt_version}
            )
            return plan, usage

    def _loop(self, message: str, tools: OpenAiAgentTools) -> AgentPlan:
        new_items: list[ResponseInputItemParam] = [{"role": "user", "content": message}]
        previous_response_id: str | None = None

        for _ in range(self._max_turns):
            with self._tracer.call(
                "agent", self._model, self._prompt_version, self._pricing
            ) as call:
                try:
                    response = self._client.responses.parse(
                        model=self._model,
                        instructions=self._instructions,
                        input=new_items,
                        tools=tools.definitions(),
                        text_format=AgentPlan,
                        reasoning=self._reasoning if self._reasoning is not None else openai.omit,
                        previous_response_id=previous_response_id or openai.omit,
                    )
                except openai.APIError as error:
                    raise UpstreamError(f"The agent failed: {type(error).__name__}") from error
                if response.usage is not None:
                    call.tokens(response.usage.input_tokens, response.usage.output_tokens)
                if response.status != "completed":
                    raise UpstreamError(f"The agent stopped early: {response.status}")

            new_items = tools.answer(response.output)
            if not new_items:
                if response.output_parsed is None:
                    raise UpstreamError("The agent finished without a plan.")
                return response.output_parsed
            previous_response_id = response.id

        raise UpstreamError(f"The agent did not finish within {self._max_turns} turns.")
