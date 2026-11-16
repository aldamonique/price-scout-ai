import type { EvalRun, LlmCall, Overview, RequestSummary } from '../api/types'

export function summary(overrides: Partial<RequestSummary> = {}): RequestSummary {
  return {
    id: 'r1',
    description: 'Living room sofa and TV stand',
    market: { country: 'br', language: 'pt-br', currency: 'BRL' },
    budget: 3000,
    status: 'done',
    total: 2277.49,
    item_count: 3,
    created_at: '2026-11-16T12:00:00Z',
    ...overrides,
  }
}

export function call(overrides: Partial<LlmCall> = {}): LlmCall {
  return {
    id: 'c1',
    request_id: 'r1',
    task: 'agent',
    model: 'agent-model',
    prompt_version: 'v3',
    input_tokens: 1000,
    output_tokens: 100,
    cost_usd: 0.003,
    latency_ms: 1240,
    ok: true,
    error: null,
    created_at: '2026-11-16T12:00:00Z',
    ...overrides,
  }
}

export function evalRun(overrides: Partial<EvalRun> = {}): EvalRun {
  const metric = { precision: 0.9, recall: 0.9, f1: 0.9 }
  return {
    run_id: 'run-glossary',
    created_at: '2026-11-16T12:00:00Z',
    judge_model: 'judge-model',
    prompt_version: 'v2',
    glossary: true,
    cases: 13,
    failed_cases: 0,
    listings: 106,
    decision_accuracy: 0.92,
    discard: metric,
    grouping: metric,
    input_tokens: 40000,
    output_tokens: 9000,
    cost_usd: 0.085,
    results: [],
    ...overrides,
  }
}

export const OVERVIEW: Overview = {
  runs: {
    requests: 4,
    done: 3,
    failed: 1,
    in_progress: 0,
    success_rate: 0.75,
    avg_duration_s: 92.4,
    p95_duration_s: 140,
    total_cost_usd: 0.27,
    avg_cost_usd: 0.09,
  },
  llm: {
    calls: 40,
    failed_calls: 2,
    unpriced_calls: 0,
    error_rate: 0.05,
    input_tokens: 120_000,
    output_tokens: 18_000,
    cost_usd: 0.27,
    avg_latency_ms: 2100,
  },
  by_version: [
    {
      task: 'agent',
      model: 'agent-model',
      prompt_version: 'v3',
      calls: 30,
      failed_calls: 1,
      input_tokens: 100_000,
      output_tokens: 15_000,
      cost_usd: 0.25,
      avg_latency_ms: 2400,
      p95_latency_ms: 5100,
    },
  ],
  daily: [
    { day: '2026-11-15', calls: 25, input_tokens: 80_000, output_tokens: 10_000, cost_usd: 0.17 },
    { day: '2026-11-16', calls: 15, input_tokens: 40_000, output_tokens: 8_000, cost_usd: 0.1 },
  ],
  tools: [{ tool: 'search_offers', calls: 12, failed_calls: 1, avg_duration_ms: 18000, p95_duration_ms: 31000 }],
  stages: [
    { stage: 'judge', searches: 12, avg_ms: 14000, p95_ms: 22000 },
    { stage: 'fetch', searches: 12, avg_ms: 4000, p95_ms: 9000 },
  ],
  recent_failures: [
    {
      request_id: 'r4',
      description: 'A queen bed',
      error: 'SerpApi failed (401)',
      created_at: '2026-11-16T11:00:00Z',
    },
  ],
}
