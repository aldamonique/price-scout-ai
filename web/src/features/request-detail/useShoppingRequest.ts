import { useEffect, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { ShoppingRequest } from '../../api/types'
import { REQUEST_POLL_MS } from '../../config'

export function isFinished(request: ShoppingRequest): boolean {
  return request.status === 'done' || request.status === 'failed'
}

export function useShoppingRequest(requestId: string | undefined) {
  const [request, setRequest] = useState<ShoppingRequest | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (requestId === undefined) return

    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined

    async function poll(id: string) {
      try {
        const current = await api.getRequest(id, controller.signal)
        setRequest(current)
        setError(null)
        if (!isFinished(current)) {
          timer = setTimeout(() => void poll(id), REQUEST_POLL_MS)
        }
      } catch (reason) {
        if (controller.signal.aborted) return
        if (reason instanceof ApiError && reason.status === 404) {
          setError('This shopping request does not exist.')
          return
        }
        setError('Connection lost. Trying again...')
        timer = setTimeout(() => void poll(id), REQUEST_POLL_MS * 2)
      }
    }

    void poll(requestId)
    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [requestId])

  return { request, error }
}
