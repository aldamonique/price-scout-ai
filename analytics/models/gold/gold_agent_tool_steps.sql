with steps as (

    select
        id as request_id,
        unnest(
            from_json(
                steps,
                '[{"number": "INTEGER", "kind": "VARCHAR", "tool": "VARCHAR",
                   "duration_ms": "INTEGER", "ok": "BOOLEAN"}]'
            )
        ) as step
    from {{ source('app', 'shopping_requests') }}

)

select
    request_id,
    step.number as step_number,
    step.kind,
    step.tool,
    step.duration_ms,
    step.ok
from steps
