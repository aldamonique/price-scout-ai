import { afterEach, describe, expect, it, vi } from 'vitest'

import { summary } from '../test/fixtures'
import { api, ApiError } from './client'
import { ResponseShapeError } from './validate'

function respond(status: number, body?: unknown) {
  return vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), { status }),
  )
}

describe('api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('deletes a request with DELETE and accepts an empty 204 answer', async () => {
    const fetch = respond(204)

    await expect(api.deleteRequest('r 1')).resolves.toBeUndefined()

    expect(fetch).toHaveBeenCalledWith('/api/shopping-requests/r%201', expect.objectContaining({ method: 'DELETE' }))
  })

  it('turns an error answer into an ApiError with the API message', async () => {
    respond(409, { detail: 'This request is still running.' })

    await expect(api.deleteRequest('r1')).rejects.toEqual(new ApiError(409, 'This request is still running.'))
  })

  it('returns answers that match the API contract', async () => {
    respond(200, [summary()])

    await expect(api.listRequests()).resolves.toEqual([summary()])
  })

  it('rejects an answer that breaks the API contract', async () => {
    respond(200, [{ ...summary(), status: 'archived' }])

    await expect(api.listRequests()).rejects.toThrow(ResponseShapeError)
  })

  it('rejects an answer with a missing field and says where', async () => {
    const { total: _total, ...withoutTotal } = summary()
    respond(200, [withoutTotal])

    await expect(api.listRequests()).rejects.toThrow(/total/)
  })
})
