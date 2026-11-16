import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { OVERVIEW } from '../../test/fixtures'
import { DailyUsageChart } from './DailyUsageChart'

describe('DailyUsageChart', () => {
  it('describes each day for screen readers in the chosen metric', () => {
    render(<DailyUsageChart daily={OVERVIEW.daily} />)

    expect(screen.getByLabelText('Nov 15: $0.17')).toBeTruthy()

    fireEvent.click(screen.getByRole('tab', { name: 'Calls' }))

    expect(screen.getByLabelText('Nov 15: 25')).toBeTruthy()
  })

  it('shows a tooltip for the bar under the pointer', () => {
    render(<DailyUsageChart daily={OVERVIEW.daily} />)

    fireEvent.mouseEnter(screen.getByLabelText('Nov 16: $0.10'))

    expect(screen.getByRole('tooltip').textContent).toContain('15 calls')
  })

  it('explains an empty chart', () => {
    render(<DailyUsageChart daily={[]} />)

    expect(screen.getByText(/No model calls yet/)).toBeTruthy()
  })
})
