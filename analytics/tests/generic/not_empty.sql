{% test not_empty(model) %}
{{ config(severity = 'error' if var('ci_fixtures', false) else 'warn') }}

select 'no rows' as problem
where not exists (select 1 from {{ model }})

{% endtest %}
