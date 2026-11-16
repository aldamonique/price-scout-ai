{{ config(enabled = var('ci_fixtures', false)) }}

with expected (search_id, offer_id, title, store, price, url, installment_months) as (

    values
        ('ci-keyboard', 'o1', 'Teclado Mecânico Redragon Kumara Rosa', 'KaBuM!', 249.9, 'https://example.com/kabum/kumara', 10),
        ('ci-keyboard', 'o2', 'Teclado Redragon Kumara Rosa ABNT2', 'Amazon', 279.0, 'https://example.com/amazon/kumara', null),
        ('ci-keyboard', 'o3', 'Teclado Redragon Kumara', 'Amazon', 299.0, 'https://example.com/amazon/kumara-b', null),
        ('ci-keyboard', 'o4', 'Kit Keycaps Rosa', 'Shopee', 59.9, 'https://example.com/shopee/keycaps', null),
        ('ci-book', 'o1', 'Mrs. Dalloway - Virginia Woolf (Brochura)', 'Amazon', 9.9, 'https://example.com/amazon/dalloway', null),
        ('ci-book', 'o2', 'Mrs Dalloway Brochura', 'Estante Virtual', 18.5, 'https://example.com/ev/dalloway', null),
        ('ci-book', 'o3', 'Ebook - Mrs Dalloway', 'publica.la', 6.21, 'https://example.com/publica/dalloway', null)

),

actual as (

    select search_id, offer_id, title, store, price, url, installment_months
    from {{ ref('silver_offers') }}
    where search_id like 'ci-%'

)

(select 'missing' as problem, * from expected except select 'missing', * from actual)
union all
(select 'unexpected' as problem, * from actual except select 'unexpected', * from expected)
