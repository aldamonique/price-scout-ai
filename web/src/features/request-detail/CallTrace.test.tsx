import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api/client'
import { call } from '../../test/fixtures'
import { CallList, CallTrace } from './CallTrace'

describe('CallList', () => {
  it('shows each call with its latency, tokens and cost', () => {
    render(<CallList calls={[call()]} />)

    expect(screen.getByText('agent')).toBeTruthy()
    expect(screen.getByText(/1.2 s · 1,000 in \/ 100 out · \$0.003/)).toBeTruthy()
  })

  it('marks a failed call and shows why', () => {
    render(<CallList calls={[call({ ok: false, error: 'rate limited', cost_usd: null })]} />)

    expect(screen.getByLabelText('failed')).toBeTruthy()
    expect(screen.getByText('rate limited')).toBeTruthy()
    expect(screen.getByText(/no price/)).toBeTruthy()
  })
})

describe('CallTrace', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads the calls of the request', async () => {
    const getRequestCalls = vi.spyOn(api, 'getRequestCalls').mockResolvedValue([call(), call({ id: 'c2', task: 'judge' })])

    render(<CallTrace requestId="r1" />)
    await act(async () => {})

    expect(getRequestCalls).toHaveBeenCalledWith('r1', expect.any(AbortSignal))
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
  })

  it('says when no call was recorded', async () => {
    vi.spyOn(api, 'getRequestCalls').mockResolvedValue([])

    render(<CallTrace requestId="r1" />)
    await act(async () => {})

    expect(screen.getByText('No calls recorded for this request.')).toBeTruthy()
  })
})
