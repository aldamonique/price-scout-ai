from price_scout.domain.catalog.models import Market, Product
from price_scout.domain.formatting import money, plural
from price_scout.domain.shopping_request.models import (
    AgentPlan,
    AgentUsage,
    PlanItem,
    SearchStats,
    ShoppingPlan,
)


def fits(product: Product, max_width_cm: float | None) -> bool | None:
    if max_width_cm is None or product.width_cm is None:
        return None
    return product.width_cm <= max_width_cm


def savings(product: Product) -> float:
    prices = [offer.price for offer in product.offers]
    if len(prices) < 2:
        return 0.0
    return round(max(prices) - min(prices), 2)


def build_plan(
    agent_plan: AgentPlan,
    known_products: dict[str, Product],
    market: Market,
    budget: float | None,
    stats: SearchStats,
    usage: AgentUsage,
) -> ShoppingPlan:
    items: list[PlanItem] = []
    unmet = list(agent_plan.unmet)
    for choice in agent_plan.choices:
        product = known_products.get(choice.product_id)
        if product is None:
            unmet.append(choice.item)
            continue
        items.append(
            PlanItem(
                item=choice.item,
                product=product,
                reason=choice.reason,
                differences=choice.differences,
                max_width_cm=choice.max_width_cm,
                fits=fits(product, choice.max_width_cm),
                savings=savings(product),
            )
        )

    total = round(sum(item.product.min_price for item in items), 2)
    return ShoppingPlan(
        market=market,
        budget=budget,
        total=total,
        leftover=None if budget is None else round(budget - total, 2),
        items=items,
        unmet=unmet,
        insights=summarize(items, budget, total, market.currency),
        stats=stats,
        usage=usage,
    )


def summarize(
    items: list[PlanItem], budget: float | None, total: float, currency: str
) -> list[str]:
    insights: list[str] = []

    if budget is None:
        insights.append(f"No budget was set; the plan totals {money(total, currency)}.")
    elif total <= budget:
        insights.append(f"The plan is {money(budget - total, currency)} under budget.")
    else:
        insights.append(f"The plan is {money(total - budget, currency)} over budget.")

    total_savings = sum(item.savings for item in items)
    if total_savings > 0:
        insights.append(f"Comparing stores saves up to {money(total_savings, currency)}.")

    checked = [item for item in items if item.fits is not None]
    if checked:
        fitting = sum(1 for item in checked if item.fits)
        insights.append(f"{fitting} of {plural(len(checked), 'item')} with a size limit fit.")

    unknown = [
        item.item
        for item in items
        if item.max_width_cm is not None and item.product.width_cm is None
    ]
    if unknown:
        insights.append(f"No measurements in the listing: {', '.join(unknown)}. Check first.")

    return insights
