import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PlanItem } from '../../api/types'
import { PriceComparator } from './PriceComparator'

const ITEM: PlanItem = {
  item: 'Sofa',
  reason: 'Fits the wall.',
  savings: 50,
  product: {
    id: 'p1',
    name: '3-Seat Sofa',
    category: 'furniture',
    min_price: 1299,
    store_count: 2,
    offers: [
      { store: 'Mobly', price: 1299, installment_months: 10, installment_amount: 129.9 },
      { store: 'Etna', price: 1349 },
    ],
  },
}

describe('PriceComparator', () => {
  it('lists each store cheapest first, with installments when the store offers them', () => {
    render(<PriceComparator item={ITEM} currency="BRL" />)

    expect(screen.getByText('Lowest price')).toBeTruthy()
    expect(screen.getByText('or 10× R$129.90')).toBeTruthy()
    expect(screen.getAllByText(/^or /)).toHaveLength(1)
    expect(screen.getByText('R$50.00')).toBeTruthy()
  })

  it('asks for a selection when there is none', () => {
    render(<PriceComparator item={null} currency="BRL" />)

    expect(screen.getByText('Select an item of the plan to compare stores.')).toBeTruthy()
  })
})
