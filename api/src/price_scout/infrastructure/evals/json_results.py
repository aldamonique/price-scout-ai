from pathlib import Path

from price_scout.domain.observability.models import EvalRun


class JsonEvalResults:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def runs(self) -> list[EvalRun]:
        if not self._directory.exists():
            return []
        runs = [
            EvalRun.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self._directory.glob("*.json")
        ]
        return sorted(runs, key=lambda run: run.created_at, reverse=True)
