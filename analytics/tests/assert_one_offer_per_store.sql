select product_id, store, count(*) as offers
from {{ ref('gold_product_offers') }}
group by product_id, store
having count(*) > 1
