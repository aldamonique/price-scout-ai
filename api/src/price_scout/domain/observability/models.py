from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

LlmTask = Literal["agent", "judge"]


class LlmCall(BaseModel):
    id: str
    request_id: str | None
    task: LlmTask
    model: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    latency_ms: int
    ok: bool
    error: str | None
    created_at: datetime


class RunStats(BaseModel):
    requests: int
    done: int
    failed: int
    in_progress: int
    success_rate: float | None
    avg_duration_s: float | None
    p95_duration_s: float | None
    total_cost_usd: float | None
    avg_cost_usd: float | None


class LlmStats(BaseModel):
    calls: int
    failed_calls: int
    unpriced_calls: int
    error_rate: float | None
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    avg_latency_ms: float | None


class VersionStats(BaseModel):
    task: LlmTask
    model: str
    prompt_version: str
    calls: int
    failed_calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    avg_latency_ms: float
    p95_latency_ms: float


class DailyUsage(BaseModel):
    day: date
    calls: int
    input_tokens: int
    output_tokens: int
    cost_usd: float | None


class ToolStats(BaseModel):
    tool: str
    calls: int
    failed_calls: int
    avg_duration_ms: float
    p95_duration_ms: float


class StageStats(BaseModel):
    stage: str
    searches: int
    avg_ms: float
    p95_ms: float


class FailedRun(BaseModel):
    request_id: str
    description: str
    error: str | None
    created_at: datetime


class Overview(BaseModel):
    runs: RunStats
    llm: LlmStats
    by_version: list[VersionStats]
    daily: list[DailyUsage]
    tools: list[ToolStats]
    stages: list[StageStats]
    recent_failures: list[FailedRun]


class Metric(BaseModel):
    precision: float
    recall: float
    f1: float


class CaseResult(BaseModel):
    case_id: str
    listings: int
    correct_decisions: int
    discard: Metric
    grouping: Metric
    error: str | None = None


class EvalRun(BaseModel):
    run_id: str
    created_at: datetime
    judge_model: str
    prompt_version: str
    glossary: bool
    cases: int
    failed_cases: int = 0
    listings: int
    decision_accuracy: float
    discard: Metric
    grouping: Metric
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    results: list[CaseResult]
