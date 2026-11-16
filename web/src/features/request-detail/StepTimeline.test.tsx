import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { AgentStep } from '../../api/types'
import { StepTimeline } from './StepTimeline'

const STEPS: AgentStep[] = [
  { number: 1, kind: 'plan', tool: 'plan_budget', summary: '3 items', duration_ms: 5, ok: true },
  { number: 2, kind: 'replan', tool: 'plan_budget', summary: 'moved R$ 300', duration_ms: 4, ok: true },
]

describe('StepTimeline', () => {
  it('shows each step with its title and summary', () => {
    render(<StepTimeline steps={STEPS} />)

    expect(screen.getByText('Planned the budget')).toBeTruthy()
    expect(screen.getByText('Re-planned')).toBeTruthy()
    expect(screen.getByText('moved R$ 300')).toBeTruthy()
  })

  it('tells the user the agent is still working', () => {
    render(<StepTimeline steps={[]} working />)

    expect(screen.getByText('Reading the request...')).toBeTruthy()
  })

  it('shows totals and an unavailable cost honestly', () => {
    const usage = { input_tokens: 18000, output_tokens: 400, cost_usd: null }

    render(<StepTimeline steps={STEPS} durationMs={9800} usage={usage} />)

    expect(screen.getByText(/2 steps · 9.8 s · 18,400 tokens · cost unavailable/)).toBeTruthy()
  })
})
