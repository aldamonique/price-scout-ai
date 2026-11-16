with accepted as (

    select
        judged.search_id,
        offers.country,
        judged.search_id || '-' || judged.product_key as product_id,
        offers.offer_id,
        offers.store,
        offers.price,
        offers.url,
        offers.image_url,
        offers.store_icon,
        offers.installment_months,
        offers.installment_amount
    from {{ source('app', 'judged_offers') }} as judged
    inner join {{ ref('silver_offers') }} as offers
        on judged.search_id = offers.search_id
        and judged.offer_id = offers.offer_id
    where not judged.discarded

)

select *
from accepted
qualify row_number() over (
    partition by product_id, store
    order by price, offer_id
) = 1
