from dataclasses import dataclass
from itertools import combinations

from evals.cases import Case
from price_scout.domain.catalog.models import Offer
from price_scout.domain.judgment.models import Judgment
from price_scout.domain.judgment.rules import reconcile
from price_scout.domain.observability.models import CaseResult, EvalRun, Metric


@dataclass
class Counts:
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0

    def __iadd__(self, other: "Counts") -> "Counts":
        self.true_positive += other.true_positive
        self.false_positive += other.false_positive
        self.false_negative += other.false_negative
        return self

    def metric(self) -> Metric:
        predicted = self.true_positive + self.false_positive
        actual = self.true_positive + self.false_negative
        precision = self.true_positive / predicted if predicted else 1.0
        recall = self.true_positive / actual if actual else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return Metric(precision=round(precision, 4), recall=round(recall, 4), f1=round(f1, 4))


def compare(predicted: set[object], expected: set[object]) -> Counts:
    return Counts(
        true_positive=len(predicted & expected),
        false_positive=len(predicted - expected),
        false_negative=len(expected - predicted),
    )


def same_product_pairs(groups: list[list[str]]) -> set[object]:
    return {frozenset(pair) for group in groups for pair in combinations(sorted(group), 2)}


def offers_of(case: Case) -> list[Offer]:
    return [
        Offer(offer_id=item.id, title=item.title, store=item.store, price=item.price or 0)
        for item in case.listings
    ]


@dataclass
class CaseScore:
    case_id: str
    listings: int
    correct_decisions: int
    discard: Counts
    pairs: Counts
    error: str | None = None

    def result(self) -> CaseResult:
        return CaseResult(
            case_id=self.case_id,
            listings=self.listings,
            correct_decisions=self.correct_decisions,
            discard=self.discard.metric(),
            grouping=self.pairs.metric(),
            error=self.error,
        )


def score_case(case: Case, judgment: Judgment) -> CaseScore:
    complete = reconcile(judgment, offers_of(case))
    predicted_discard = {item.offer_id for item in complete.discarded}
    expected_discard = set(case.expected.discard)
    predicted_groups = [group.offer_ids for group in complete.products]

    correct = sum(
        1
        for item in case.listings
        if (item.id in predicted_discard) == (item.id in expected_discard)
    )
    return CaseScore(
        case_id=case.id,
        listings=len(case.listings),
        correct_decisions=correct,
        discard=compare(set(predicted_discard), set(expected_discard)),
        pairs=compare(
            same_product_pairs(predicted_groups), same_product_pairs(case.expected.groups)
        ),
    )


def failed_case(case: Case, error: str) -> CaseScore:
    return CaseScore(
        case_id=case.id,
        listings=len(case.listings),
        correct_decisions=0,
        discard=compare(set(), set(case.expected.discard)),
        pairs=compare(set(), same_product_pairs(case.expected.groups)),
        error=error,
    )


@dataclass
class Totals:
    listings: int = 0
    correct_decisions: int = 0
    failed_cases: int = 0

    def __post_init__(self) -> None:
        self.discard = Counts()
        self.pairs = Counts()

    def add(self, score: CaseScore) -> None:
        self.listings += score.listings
        self.correct_decisions += score.correct_decisions
        self.discard += score.discard
        self.pairs += score.pairs
        if score.error is not None:
            self.failed_cases += 1

    @property
    def decision_accuracy(self) -> float:
        return round(self.correct_decisions / self.listings, 4) if self.listings else 0.0


def gate(run: EvalRun, min_f1: float | None) -> list[str]:
    reasons: list[str] = []
    if run.failed_cases:
        reasons.append(f"{run.failed_cases} of {run.cases} cases failed to run")
    if run.cases == 0:
        reasons.append("no case was evaluated")
    if min_f1 is not None:
        for name, metric in (("discard", run.discard), ("grouping", run.grouping)):
            if metric.f1 < min_f1:
                reasons.append(f"{name} F1 {metric.f1:.2f} is below the minimum of {min_f1}")
    return reasons
