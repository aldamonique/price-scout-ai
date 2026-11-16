select id, input_tokens, output_tokens, cost_usd, latency_ms
from {{ source('app', 'llm_calls') }}
where input_tokens < 0
   or output_tokens < 0
   or cost_usd < 0
   or latency_ms < 0
