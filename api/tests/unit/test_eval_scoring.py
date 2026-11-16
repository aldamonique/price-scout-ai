from datetime import UTC, datetime

from evals.cases import Case, load_cases
from evals.run import judge_case
from evals.scoring import Totals, failed_case, gate, score_case
from price_scout.domain.catalog.models import Offer, SearchIntent
from price_scout.domain.judgment.models import DiscardedOffer, Judgment, ProductGroup
from price_scout.domain.observability.models import EvalRun


def case() -> Case:
    return Case.model_validate(
        {
            "id": "c",
            "source": "test",
            "note": "",
            "query": "whey 900g",
            "category": "health",
            "country": "br",
            "listings": [
                {"id": i, "title": i, "store": "s", "price": 1.0} for i in ["a", "b", "c", "d"]
            ],
            "expected": {"groups": [["a", "b"], ["c"]], "discard": ["d"]},
        }
    )


def group(*ids: str) -> ProductGroup:
    return ProductGroup(
        name="x",
        category="health",
        width_cm=None,
        depth_cm=None,
        height_cm=None,
        offer_ids=list(ids),
    )


def test_a_perfect_judgment_scores_one_everywhere() -> None:
    judgment = Judgment(
        products=[group("a", "b"), group("c")],
        discarded=[DiscardedOffer(offer_id="d", reason="1 kg")],
    )

    score = score_case(case(), judgment).result()

    assert score.correct_decisions == 4
    assert (score.discard.f1, score.grouping.f1) == (1.0, 1.0)


def test_merging_different_products_costs_grouping_precision() -> None:
    judgment = Judgment(
        products=[group("a", "b", "c")], discarded=[DiscardedOffer(offer_id="d", reason="")]
    )

    grouping = score_case(case(), judgment).result().grouping

    assert (grouping.precision, grouping.recall) == (round(1 / 3, 4), 1.0)


def test_a_listing_the_judge_forgot_counts_as_discarded() -> None:
    judgment = Judgment(
        products=[group("a", "b")], discarded=[DiscardedOffer(offer_id="d", reason="")]
    )

    result = score_case(case(), judgment).result()

    assert result.correct_decisions == 3
    assert result.discard.precision == 0.5


def test_totals_are_micro_averaged_over_cases() -> None:
    totals = Totals()
    perfect = Judgment(
        products=[group("a", "b"), group("c")], discarded=[DiscardedOffer(offer_id="d", reason="")]
    )
    sloppy = Judgment(products=[group("a"), group("b"), group("c"), group("d")], discarded=[])

    totals.add(score_case(case(), perfect))
    totals.add(score_case(case(), sloppy))

    assert totals.decision_accuracy == 0.875
    assert totals.discard.metric().recall == 0.5
    assert totals.pairs.metric().recall == 0.5


def test_every_labeled_case_is_consistent() -> None:
    for labeled in load_cases():
        ids = [item.id for item in labeled.listings]
        grouped = [i for g in labeled.expected.groups for i in g]
        labeled_ids = grouped + labeled.expected.discard
        assert sorted(labeled_ids) == sorted(ids), labeled.id
        assert len(set(ids)) == len(ids), labeled.id


PERFECT = Judgment(
    products=[group("a", "b"), group("c")], discarded=[DiscardedOffer(offer_id="d", reason="")]
)


def run_of(totals: Totals, cases: int) -> EvalRun:
    return EvalRun(
        run_id="r",
        created_at=datetime(2026, 11, 16, tzinfo=UTC),
        judge_model="m",
        prompt_version="v2",
        glossary=True,
        cases=cases,
        failed_cases=totals.failed_cases,
        listings=totals.listings,
        decision_accuracy=totals.decision_accuracy,
        discard=totals.discard.metric(),
        grouping=totals.pairs.metric(),
        input_tokens=0,
        output_tokens=0,
        cost_usd=None,
        results=[],
    )


class BrokenJudge:
    version = "m/v2/glossary"

    def judge(self, intent: SearchIntent, offers: list[Offer]) -> Judgment:
        raise TimeoutError("judge timed out")


def test_a_judge_error_becomes_a_failed_case() -> None:
    score = judge_case(BrokenJudge(), case())

    assert score.error == "TimeoutError: judge timed out"
    assert score.correct_decisions == 0


def test_a_failed_case_counts_every_expected_answer_as_missed() -> None:
    totals = Totals()
    totals.add(score_case(case(), PERFECT))
    totals.add(failed_case(case(), "TimeoutError"))

    assert totals.failed_cases == 1
    assert totals.decision_accuracy == 0.5
    assert totals.discard.metric().recall == 0.5
    assert totals.pairs.metric().recall == 0.5
    assert totals.discard.metric().f1 < 1


def test_a_run_where_every_case_failed_scores_zero() -> None:
    totals = Totals()
    totals.add(failed_case(case(), "RateLimitError"))
    totals.add(failed_case(case(), "RateLimitError"))

    run = run_of(totals, cases=2)

    assert (run.discard.f1, run.grouping.f1, run.decision_accuracy) == (0.0, 0.0, 0.0)
    assert gate(run, min_f1=0.8) != []
    assert gate(run, min_f1=None) != []


def test_a_run_with_errors_never_passes_even_above_the_minimum() -> None:
    totals = Totals()
    for _ in range(9):
        totals.add(score_case(case(), PERFECT))
    totals.add(failed_case(case(), "APIConnectionError"))

    run = run_of(totals, cases=10)

    assert run.discard.f1 > 0.8
    assert gate(run, min_f1=0.8) == ["1 of 10 cases failed to run"]


def test_a_clean_run_passes_only_at_or_above_the_minimum() -> None:
    totals = Totals()
    totals.add(score_case(case(), PERFECT))

    assert gate(run_of(totals, cases=1), min_f1=0.8) == []
    assert gate(run_of(totals, cases=1), min_f1=0.0) == []
    sloppy = Totals()
    sloppy.add(score_case(case(), Judgment(products=[group("a", "b", "c", "d")], discarded=[])))
    assert len(gate(run_of(sloppy, cases=1), min_f1=0.8)) == 2


def test_an_empty_run_does_not_pass() -> None:
    assert gate(run_of(Totals(), cases=0), min_f1=None) == ["no case was evaluated"]
