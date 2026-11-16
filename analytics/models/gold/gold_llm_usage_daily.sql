select
    cast(created_at as date) as day,
    task,
    model,
    prompt_version,
    count(*) as calls,
    count(*) filter (where not ok) as failed_calls,
    count(*) filter (where cost_usd is null) as unpriced_calls,
    sum(input_tokens) as input_tokens,
    sum(output_tokens) as output_tokens,
    sum(cost_usd) as cost_usd,
    avg(latency_ms) as avg_latency_ms,
    quantile_cont(latency_ms, 0.95) as p95_latency_ms
from {{ source('app', 'llm_calls') }}
group by all
