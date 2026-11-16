import { useEffect, useState } from 'react'

import { api } from '../../api/client'
import type { LlmCall } from '../../api/types'

export function useRequestCalls(requestId: string) {
  const [calls, setCalls] = useState<LlmCall[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    api
      .getRequestCalls(requestId, controller.signal)
      .then(setCalls)
      .catch(() => {
        if (!controller.signal.aborted) setError('Could not load the model calls.')
      })
    return () => controller.abort()
  }, [requestId])

  return { calls, error }
}
