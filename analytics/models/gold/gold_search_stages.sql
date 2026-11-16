with steps as (

    select
        id as request_id,
        unnest(
            from_json(
                steps,
                '[{"number": "INTEGER", "tool": "VARCHAR", "stage_ms": "MAP(VARCHAR, INTEGER)"}]'
            )
        ) as step
    from {{ source('app', 'shopping_requests') }}

),

stages as (

    select
        request_id,
        step.number as step_number,
        unnest(map_entries(step.stage_ms)) as entry
    from steps
    where step.stage_ms is not null

)

select
    request_id,
    step_number,
    entry.key as stage,
    entry.value as duration_ms
from stages
