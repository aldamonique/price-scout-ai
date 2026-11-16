import { describe, expect, it } from 'vitest'

import type { ShoppingPlan } from '../../api/types'
import { planKpis } from './kpis'

const PLAN: ShoppingPlan = {
  market: { country: 'br', language: 'pt-br', currency: 'BRL' },
  budget: 3000,
  total: 1299,
  leftover: 1701,
  unmet: [],
  insights: [],
  stats: { searches: 2, listings: 80, discarded: 9 },
  usage: { input_tokens: 18000, output_tokens: 400, cost_usd: 0.04 },
  items: [
    {
      item: 'Sofa',
      reason: '',
      savings: 50,
      product: {
        id: 'p1',
        name: 'Sofa',
        category: 'furniture',
        min_price: 1299,
        store_count: 2,
        offers: [
          { store: 'Mobly', price: 1299 },
          { store: 'Etna', price: 1349 },
        ],
      },
    },
  ],
}

describe('planKpis', () => {
  it('shows a dash before there is a plan', () => {
    expect(planKpis(null).map((kpi) => kpi.value)).toEqual(['—', '—', '—', '—'])
  })

  it('counts listings, distinct stores, savings and cost', () => {
    expect(planKpis(PLAN).map((kpi) => kpi.value)).toEqual(['80', '2', 'R$50.00', '$0.04'])
    expect(planKpis(PLAN)[0]?.hint).toBe('9 discarded · 2 searches')
  })
})
