from datetime import UTC, datetime
from pathlib import Path

from price_scout.domain.observability.models import EvalRun
from price_scout.infrastructure.evals.json_results import JsonEvalResults


def run(run_id: str, hour: int) -> EvalRun:
    metric = {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    return EvalRun.model_validate(
        {
            "run_id": run_id,
            "created_at": datetime(2026, 11, 16, hour, tzinfo=UTC),
            "judge_model": "m",
            "prompt_version": "v2",
            "glossary": True,
            "cases": 1,
            "listings": 4,
            "decision_accuracy": 1.0,
            "discard": metric,
            "grouping": metric,
            "input_tokens": 10,
            "output_tokens": 2,
            "cost_usd": None,
            "results": [],
        }
    )


def test_runs_are_read_newest_first(tmp_path: Path) -> None:
    for run_id, hour in [("old", 9), ("new", 11)]:
        (tmp_path / f"{run_id}.json").write_text(run(run_id, hour).model_dump_json())

    assert [r.run_id for r in JsonEvalResults(tmp_path).runs()] == ["new", "old"]


def test_a_missing_folder_has_no_runs(tmp_path: Path) -> None:
    assert JsonEvalResults(tmp_path / "missing").runs() == []
