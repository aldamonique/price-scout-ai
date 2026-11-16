import type { ShoppingPlan } from '../../api/types'
import { integer, money, usd } from '../../lib/format'

export interface Kpi {
  label: string
  value: string
  hint: string
}

const EMPTY = '—'

export function planKpis(plan: ShoppingPlan | null | undefined): Kpi[] {
  if (!plan) {
    return [
      { label: 'Listings', value: EMPTY, hint: 'reviewed on Google Shopping' },
      { label: 'Stores', value: EMPTY, hint: 'compared in the plan' },
      { label: 'Savings', value: EMPTY, hint: 'vs. priciest store' },
      { label: 'Agent cost', value: EMPTY, hint: 'model tokens' },
    ]
  }

  const { stats, usage, market } = plan
  const stores = new Set(plan.items.flatMap((item) => item.product.offers.map((offer) => offer.store)))
  const savings = plan.items.reduce((sum, item) => sum + item.savings, 0)

  return [
    {
      label: 'Listings',
      value: integer(stats.listings),
      hint: `${integer(stats.discarded)} discarded · ${integer(stats.searches)} searches`,
    },
    { label: 'Stores', value: integer(stores.size), hint: 'compared in the plan' },
    { label: 'Savings', value: money(savings, market.currency), hint: 'vs. priciest store' },
    {
      label: 'Agent cost',
      value: usage.cost_usd == null ? EMPTY : usd(usage.cost_usd),
      hint: `${integer(usage.input_tokens + usage.output_tokens)} tokens`,
    },
  ]
}
