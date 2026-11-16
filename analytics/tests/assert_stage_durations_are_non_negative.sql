select request_id, step_number, stage, duration_ms
from {{ ref('gold_search_stages') }}
where duration_ms < 0
