import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PlanItem } from '../../api/types'
import { PlanItemCard } from './PlanItemCard'

const ITEM: PlanItem = {
  item: 'Mechanical keyboard',
  reason: 'Pink mechanical keyboard sold by 3 stores.',
  savings: 40,
  product: {
    id: 'p1',
    name: 'Redragon Kumara Pink',
    category: 'electronics',
    min_price: 249.9,
    store_count: 3,
    offers: [{ store: 'KaBuM!', price: 249.9 }],
  },
}

function renderCard(item: PlanItem) {
  render(<PlanItemCard item={item} currency="BRL" selected={false} onSelect={() => {}} />)
}

describe('PlanItemCard', () => {
  it('flags a close match and says what differs from the request', () => {
    renderCard({ ...ITEM, differences: 'ABNT2 layout not confirmed' })

    expect(screen.getByText('Similar match')).toBeTruthy()
    expect(screen.getByText('ABNT2 layout not confirmed')).toBeTruthy()
  })

  it('shows no flag when the product matches the request', () => {
    renderCard({ ...ITEM, differences: null })

    expect(screen.queryByText('Similar match')).toBeNull()
  })
})
