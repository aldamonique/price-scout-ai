import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError } from '../../api/client'
import type { ShoppingRequest } from '../../api/types'
import { REQUEST_POLL_MS } from '../../config'
import { useShoppingRequest } from './useShoppingRequest'

function shoppingRequest(status: ShoppingRequest['status'], steps = 0): ShoppingRequest {
  return {
    id: 'r1',
    description: 'furnish the living room',
    market: { country: 'br', language: 'pt-br', currency: 'BRL' },
    budget: 3000,
    preferences: {},
    status,
    steps: Array.from({ length: steps }, (_, index) => ({
      number: index + 1,
      kind: 'search',
      tool: 'search_offers',
      summary: 'ok',
      duration_ms: 10,
      ok: true,
    })),
    plan: null,
    error: null,
    created_at: '2026-11-15T12:00:00Z',
    updated_at: '2026-11-15T12:00:30Z',
  }
}

async function nextPoll() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(REQUEST_POLL_MS)
  })
}

describe('useShoppingRequest', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('polls until the request finishes, then stops', async () => {
    const getRequest = vi
      .spyOn(api, 'getRequest')
      .mockResolvedValueOnce(shoppingRequest('running', 1))
      .mockResolvedValueOnce(shoppingRequest('running', 2))
      .mockResolvedValueOnce(shoppingRequest('done', 3))

    const { result } = renderHook(() => useShoppingRequest('r1'))
    await act(async () => {})
    expect(result.current.request?.steps).toHaveLength(1)

    await nextPoll()
    await nextPoll()
    expect(result.current.request?.status).toBe('done')

    await nextPoll()
    expect(getRequest).toHaveBeenCalledTimes(3)
  })

  it('keeps trying after a dropped connection', async () => {
    vi.spyOn(api, 'getRequest')
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce(shoppingRequest('done'))

    const { result } = renderHook(() => useShoppingRequest('r1'))
    await act(async () => {})
    expect(result.current.error).toBe('Connection lost. Trying again...')

    await nextPoll()
    await nextPoll()
    expect(result.current.request?.status).toBe('done')
    expect(result.current.error).toBeNull()
  })

  it('stops and explains when the request does not exist', async () => {
    const getRequest = vi
      .spyOn(api, 'getRequest')
      .mockRejectedValue(new ApiError(404, 'No shopping request'))

    const { result } = renderHook(() => useShoppingRequest('nope'))
    await act(async () => {})
    await nextPoll()

    expect(result.current.error).toBe('This shopping request does not exist.')
    expect(getRequest).toHaveBeenCalledTimes(1)
  })

  it('does nothing without a request id', () => {
    const getRequest = vi.spyOn(api, 'getRequest')

    renderHook(() => useShoppingRequest(undefined))

    expect(getRequest).not.toHaveBeenCalled()
  })
})
