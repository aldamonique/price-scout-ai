select search_id, offer_id, price
from {{ ref('silver_offers') }}
where price < 1 or price > 200000
