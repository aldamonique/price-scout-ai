with groups as (

    select distinct
        search_id,
        search_id || '-' || product_key as product_id,
        product_name as name,
        case
            when category in ('sofa', 'table', 'tv_stand', 'bed') then 'furniture'
            else category
        end as category,
        width_cm,
        depth_cm,
        height_cm
    from {{ source('app', 'judged_offers') }}
    where not discarded

),

prices as (

    select
        product_id,
        any_value(country) as country,
        min(price) as min_price,
        count(*) as store_count,
        arg_min(image_url, price) as image_url
    from {{ ref('gold_product_offers') }}
    group by product_id

)

select
    groups.search_id,
    prices.country,
    groups.product_id,
    groups.name,
    groups.category,
    groups.width_cm,
    groups.depth_cm,
    groups.height_cm,
    prices.image_url,
    prices.min_price,
    prices.store_count
from groups
inner join prices on groups.product_id = prices.product_id
