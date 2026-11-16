with calls as (

    select
        request_id,
        count(*) as llm_calls,
        count(*) filter (where not ok) as failed_llm_calls,
        sum(input_tokens) as input_tokens,
        sum(output_tokens) as output_tokens,
        sum(cost_usd) as cost_usd
    from {{ source('app', 'llm_calls') }}
    where request_id is not null
    group by request_id

)

select
    requests.id as request_id,
    requests.status,
    requests.description,
    requests.error,
    json_extract_string(requests.market, '$.country') as country,
    requests.budget,
    cast(json_extract(requests.plan, '$.total') as double) as total,
    json_extract_string(requests.plan, '$.usage.agent_model') as agent_model,
    json_extract_string(requests.plan, '$.usage.agent_prompt_version') as agent_prompt_version,
    json_array_length(requests.steps) as steps,
    requests.created_at,
    requests.updated_at,
    date_diff('millisecond', requests.created_at, requests.updated_at) / 1000.0 as duration_s,
    coalesce(calls.llm_calls, 0) as llm_calls,
    coalesce(calls.failed_llm_calls, 0) as failed_llm_calls,
    coalesce(calls.input_tokens, 0) as input_tokens,
    coalesce(calls.output_tokens, 0) as output_tokens,
    calls.cost_usd
from {{ source('app', 'shopping_requests') }} as requests
left join calls on requests.id = calls.request_id
