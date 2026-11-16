import { useEffect, useState } from 'react'

import { api } from '../api/client'
import type { RequestSummary } from '../api/types'

const REFRESH_MS = 5000

export function useRequestHistory() {
  const [requests, setRequests] = useState<RequestSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined

    async function load() {
      try {
        const current = await api.listRequests(controller.signal)
        setRequests(current)
        setError(null)
        if (current.some((r) => r.status === 'queued' || r.status === 'running')) {
          timer = setTimeout(() => void load(), REFRESH_MS)
        }
      } catch {
        if (!controller.signal.aborted) setError('Could not load the requests. Is the API running?')
      }
    }

    void load()
    return () => {
      controller.abort()
      clearTimeout(timer)
    }
  }, [])

  return { requests, error }
}
