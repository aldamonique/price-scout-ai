import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '../api/client'
import { readAdminToken, saveAdminToken } from './adminToken'

describe('admin token', () => {
  afterEach(() => {
    window.localStorage.clear()
    vi.restoreAllMocks()
  })

  it('is saved trimmed and cleared when empty', () => {
    saveAdminToken('  secret ')
    expect(readAdminToken()).toBe('secret')

    saveAdminToken('')
    expect(readAdminToken()).toBeNull()
  })

  it('is sent as a bearer token on every API call', async () => {
    saveAdminToken('secret')
    const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('[]', { status: 200 }))

    await api.listRequests()

    const init = fetch.mock.calls[0]?.[1] as RequestInit
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer secret')
  })
})
