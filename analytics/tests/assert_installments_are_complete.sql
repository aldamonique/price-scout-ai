select search_id, offer_id, installment_months, installment_amount
from {{ ref('silver_offers') }}
where (installment_months is null) <> (installment_amount is null)
   or installment_months <= 0
   or installment_amount <= 0
