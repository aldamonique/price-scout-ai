from price_scout.domain.catalog.models import Offer
from price_scout.domain.judgment.models import DiscardedOffer, Judgment, ProductGroup

UNCLASSIFIED = "not classified by the judge"


def reconcile(judgment: Judgment, offers: list[Offer]) -> Judgment:
    pending = {offer.offer_id for offer in offers}

    products: list[ProductGroup] = []
    for group in judgment.products:
        ids = [i for i in dict.fromkeys(group.offer_ids) if i in pending]
        pending -= set(ids)
        if ids:
            products.append(group.model_copy(update={"offer_ids": ids}))

    discarded: list[DiscardedOffer] = []
    for item in judgment.discarded:
        if item.offer_id in pending:
            pending.remove(item.offer_id)
            discarded.append(item)

    discarded += [
        DiscardedOffer(offer_id=offer_id, reason=UNCLASSIFIED) for offer_id in sorted(pending)
    ]
    return Judgment(products=products, discarded=discarded)


def discard_blocked(judgment: Judgment, blocked: list[Offer], reason: str) -> Judgment:
    extra = [
        DiscardedOffer(offer_id=offer.offer_id, reason=f"{offer.store}: {reason}")
        for offer in blocked
    ]
    return judgment.model_copy(update={"discarded": [*judgment.discarded, *extra]})
