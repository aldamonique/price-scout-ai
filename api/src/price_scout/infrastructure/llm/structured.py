from dataclasses import dataclass
from typing import Protocol

import openai
from openai.types.shared_params import Reasoning
from pydantic import BaseModel

from price_scout.domain.errors import UpstreamError


@dataclass(frozen=True)
class LlmResult[T: BaseModel]:
    output: T
    input_tokens: int
    output_tokens: int


class StructuredLlm(Protocol):
    def parse[T: BaseModel](
        self, *, task: str, system: str, user: str, output_type: type[T]
    ) -> LlmResult[T]: ...


class OpenAiStructuredLlm:
    def __init__(self, client: openai.OpenAI, model: str, reasoning: Reasoning | None) -> None:
        self._client = client
        self._model = model
        self._reasoning = reasoning

    def parse[T: BaseModel](
        self, *, task: str, system: str, user: str, output_type: type[T]
    ) -> LlmResult[T]:
        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=system,
                input=user,
                text_format=output_type,
                reasoning=self._reasoning if self._reasoning is not None else openai.omit,
                store=False,
            )
        except openai.APIError as error:
            raise UpstreamError(f"LLM failed on '{task}': {type(error).__name__}") from error

        if response.status != "completed" or response.output_parsed is None:
            raise UpstreamError(f"LLM did not finish '{task}': {response.status}")

        usage = response.usage
        return LlmResult(
            output=response.output_parsed,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
        )
