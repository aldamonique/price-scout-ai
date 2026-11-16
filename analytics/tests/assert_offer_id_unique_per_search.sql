select search_id, offer_id, count(*) as copies
from {{ ref('silver_offers') }}
group by search_id, offer_id
having count(*) > 1
