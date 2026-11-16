import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ShoppingPlan } from '../../api/types'
import { BudgetBar } from './BudgetBar'

function plan(budget: number | null, total: number): ShoppingPlan {
  return {
    market: { country: 'br', language: 'pt-br', currency: 'BRL' },
    budget,
    total,
    leftover: budget == null ? null : budget - total,
    items: [],
    unmet: [],
    insights: [],
    stats: { searches: 1, listings: 10, discarded: 1 },
    usage: { input_tokens: 0, output_tokens: 0 },
  }
}

describe('BudgetBar', () => {
  it('shows how much of the budget the plan uses', () => {
    render(<BudgetBar plan={plan(3000, 1500)} />)

    expect(screen.getByRole('progressbar').getAttribute('aria-valuenow')).toBe('50')
    expect(screen.getByText('R$1,500.00 left')).toBeTruthy()
  })

  it('warns when the plan goes over the budget', () => {
    render(<BudgetBar plan={plan(1000, 1200)} />)

    expect(screen.getByText('R$200.00 over')).toBeTruthy()
  })

  it('shows only the total when no budget was set', () => {
    render(<BudgetBar plan={plan(null, 1299)} />)

    expect(screen.queryByRole('progressbar')).toBeNull()
    expect(screen.getByText(/no budget set/)).toBeTruthy()
  })
})
