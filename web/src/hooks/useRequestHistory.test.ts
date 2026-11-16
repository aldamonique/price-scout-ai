import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api/client'
import { summary } from '../test/fixtures'
import { useRequestHistory } from './useRequestHistory'

describe('useRequestHistory', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('refreshes while a request is still running, then stops', async () => {
    const listRequests = vi
      .spyOn(api, 'listRequests')
      .mockResolvedValueOnce([summary({ status: 'running', total: null })])
      .mockResolvedValueOnce([summary({ status: 'done' })])

    const { result } = renderHook(() => useRequestHistory())
    await act(async () => {})
    expect(result.current.requests?.[0]?.status).toBe('running')

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000)
    })
    expect(result.current.requests?.[0]?.status).toBe('done')

    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000)
    })
    expect(listRequests).toHaveBeenCalledTimes(2)
  })

  it('loads once when every request has finished', async () => {
    const listRequests = vi.spyOn(api, 'listRequests').mockResolvedValue([summary()])

    renderHook(() => useRequestHistory())
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000)
    })

    expect(listRequests).toHaveBeenCalledOnce()
  })
})
