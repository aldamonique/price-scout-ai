{{ config(enabled = var('ci_fixtures', false)) }}

with expected (product_id, name, category, min_price, store_count) as (

    values
        ('ci-keyboard-p1', 'Redragon Kumara Pink Mechanical Keyboard', 'electronics', 249.9, 2),
        ('ci-book-p1', 'Mrs Dalloway, paperback', 'books', 9.9, 2),
        ('ci-book-p2', 'Mrs Dalloway, e-book', 'books', 6.21, 1)

),

actual as (

    select product_id, name, category, min_price, store_count
    from {{ ref('gold_products') }}
    where search_id like 'ci-%'

)

(select 'missing' as problem, * from expected except select 'missing', * from actual)
union all
(select 'unexpected' as problem, * from actual except select 'unexpected', * from expected)
