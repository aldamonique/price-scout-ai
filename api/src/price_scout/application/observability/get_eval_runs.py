from price_scout.domain.observability.models import EvalRun
from price_scout.domain.observability.ports import EvalResults


class GetEvalRuns:
    def __init__(self, results: EvalResults) -> None:
        self._results = results

    def execute(self) -> list[EvalRun]:
        return self._results.runs()
