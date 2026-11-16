with offers as (

    select product_id, min(price) as min_price, count(*) as store_count
    from {{ ref('gold_product_offers') }}
    group by product_id

)

select products.product_id, products.min_price, offers.min_price as offers_min_price
from {{ ref('gold_products') }} as products
left join offers on products.product_id = offers.product_id
where offers.product_id is null
   or products.min_price <> offers.min_price
   or products.store_count <> offers.store_count
