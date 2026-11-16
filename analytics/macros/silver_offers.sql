{% macro silver_offers_from(bronze) %}
    with searches as (

        select search_id, country, fetched_at, payload
        from read_json(
            '{{ bronze }}',
            columns = {
                search_id: 'VARCHAR',
                country: 'VARCHAR',
                fetched_at: 'TIMESTAMPTZ',
                payload: 'JSON'
            }
        )

    ),

    results as (

        select
            search_id,
            country,
            fetched_at,
            unnest(from_json(payload -> 'shopping_results', '["JSON"]')) as result
        from searches

    ),

    typed as (

        select
            search_id,
            country,
            fetched_at,
            cast(result ->> 'position' as integer) as position,
            trim(result ->> 'title') as title,
            trim(result ->> 'source') as store,
            cast(result ->> 'extracted_price' as double) as price,
            coalesce(result ->> 'link', result ->> 'product_link') as url,
            result ->> 'thumbnail' as image_url,
            result ->> 'source_icon' as store_icon,
            cast(result -> 'installment' ->> 'period' as integer) as installment_months,
            cast(result -> 'installment' ->> 'extracted_price' as double) as installment_amount
        from results

    ),

    valid as (

        select *
        from typed
        where title is not null
          and store is not null
          and price > 0

    ),

    deduplicated as (

        select *
        from valid
        qualify row_number() over (
            partition by search_id, store, title, price
            order by position
        ) = 1

    )

    select
        search_id,
        country,
        'o' || row_number() over (partition by search_id order by position) as offer_id,
        title,
        store,
        price,
        url,
        image_url,
        store_icon,
        installment_months,
        installment_amount,
        fetched_at
    from deduplicated
{% endmacro %}
