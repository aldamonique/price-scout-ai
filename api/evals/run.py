import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from datetime import UTC, datetime
from pathlib import Path

import openai

from evals.cases import Case, load_cases
from evals.scoring import CaseScore, Totals, failed_case, gate, offers_of, score_case
from price_scout.bootstrap import pricing, reasoning
from price_scout.config import Settings
from price_scout.domain.catalog.markets import market_for
from price_scout.domain.catalog.models import SearchIntent
from price_scout.domain.judgment.ports import OfferJudge
from price_scout.domain.observability.models import EvalRun
from price_scout.infrastructure.context import load_business_context
from price_scout.infrastructure.llm.offer_judge import LlmOfferJudge
from price_scout.infrastructure.llm.structured import OpenAiStructuredLlm
from price_scout.infrastructure.llm.tracing import CallTracer, NullCallLog, ObservedLlm, tracing
from price_scout.infrastructure.llm.usage import UsageMeter

PARALLEL_CASES = 4


def judge_case(judge: OfferJudge, case: Case) -> CaseScore:
    intent = SearchIntent(query=case.query, category=case.category, market=market_for(case.country))
    try:
        judgment = judge.judge(intent, offers_of(case))
    except Exception as error:
        return failed_case(case, f"{type(error).__name__}: {error}"[:300])
    return score_case(case, judgment)


def run_variant(settings: Settings, cases: list[Case], glossary: bool) -> EvalRun:
    client = openai.OpenAI(api_key=settings.openai_api_key)
    judge_settings = settings.judge
    llm = ObservedLlm(
        OpenAiStructuredLlm(
            client, judge_settings.model, reasoning(judge_settings.reasoning_effort)
        ),
        CallTracer(NullCallLog()),
        task="judge",
        model=judge_settings.model,
        prompt_version=judge_settings.prompt_version,
        pricing=pricing(judge_settings),
    )
    judge = LlmOfferJudge(
        llm,
        load_business_context() if glossary else None,
        prompt_version=judge_settings.prompt_version,
        model=judge_settings.model,
    )

    meter = UsageMeter()
    with tracing(None, meter):
        contexts = [copy_context() for _ in cases]
        with ThreadPoolExecutor(max_workers=PARALLEL_CASES) as pool:
            outcomes = list(
                pool.map(
                    lambda pair: pair[0].run(judge_case, judge, pair[1]),
                    zip(contexts, cases, strict=True),
                )
            )

    totals = Totals()
    for outcome in outcomes:
        totals.add(outcome)
    results = [outcome.result() for outcome in outcomes]

    usage = meter.usage()
    created_at = datetime.now(UTC)
    variant = "glossary" if glossary else "no-glossary"
    return EvalRun(
        run_id=f"{created_at:%Y%m%dT%H%M%S}-{judge_settings.prompt_version}-{variant}",
        created_at=created_at,
        judge_model=judge_settings.model,
        prompt_version=judge_settings.prompt_version,
        glossary=glossary,
        cases=len(cases),
        failed_cases=totals.failed_cases,
        listings=totals.listings,
        decision_accuracy=totals.decision_accuracy,
        discard=totals.discard.metric(),
        grouping=totals.pairs.metric(),
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cost_usd=usage.cost_usd,
        results=results,
    )


def report(run: EvalRun) -> str:
    variant = "with glossary" if run.glossary else "without glossary"
    cost = "n/a" if run.cost_usd is None else f"${run.cost_usd:.4f}"
    return (
        f"{run.judge_model} {run.prompt_version} {variant}: "
        f"decisions {run.decision_accuracy:.1%} | discard F1 {run.discard.f1:.2f} | "
        f"grouping F1 {run.grouping.f1:.2f} | {run.cases} cases, {run.failed_cases} failed | "
        f"{cost}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure the offer judge on the labeled cases.")
    parser.add_argument("--variant", choices=["both", "glossary", "no-glossary"], default="both")
    parser.add_argument(
        "--min-f1", type=float, default=None, help="Fail below this F1 (glossary run)."
    )
    parser.add_argument("--case", action="append", help="Run only these case ids.")
    parser.add_argument("--out", type=Path, default=None, help="Where to save the results.")
    args = parser.parse_args()

    settings = Settings()
    cases = [c for c in load_cases() if not args.case or c.id in args.case]
    out = args.out or settings.eval_results_dir
    out.mkdir(parents=True, exist_ok=True)

    variants = {"both": [True, False], "glossary": [True], "no-glossary": [False]}[args.variant]
    failed = False
    for glossary in variants:
        run = run_variant(settings, cases, glossary)
        (out / f"{run.run_id}.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
        print(report(run))
        for result in run.results:
            if result.error:
                print(f"  {result.case_id}: {result.error}")
        reasons = gate(run, args.min_f1 if glossary else None)
        for reason in reasons:
            print(f"FAIL: {reason}")
        failed = failed or bool(reasons)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
