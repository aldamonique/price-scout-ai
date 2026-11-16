from typing import Protocol

from price_scout.domain.observability.models import EvalRun, LlmCall, Overview


class CallLog(Protocol):
    def record(self, call: LlmCall) -> None: ...

    def calls(self, request_id: str) -> list[LlmCall]: ...

    def delete_for_request(self, request_id: str) -> None: ...


class ObservabilityReader(Protocol):
    def overview(self) -> Overview: ...


class EvalResults(Protocol):
    def runs(self) -> list[EvalRun]: ...
