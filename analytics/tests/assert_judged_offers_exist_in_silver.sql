{{ config(severity = 'error' if var('ci_fixtures', false) else 'warn') }}

select judged.search_id, judged.offer_id
from {{ source('app', 'judged_offers') }} as judged
left join {{ ref('silver_offers') }} as offers
    on judged.search_id = offers.search_id
    and judged.offer_id = offers.offer_id
where offers.offer_id is null
