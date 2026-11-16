import { useEffect, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { EvalRun, Overview } from '../../api/types'

function message(reason: unknown): string {
  if (reason instanceof ApiError && (reason.status === 503 || reason.status === 401)) return reason.message
  return 'Could not load the observability data. Is the API running?'
}

export function useObservability() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [locked, setLocked] = useState(false)
  const [runs, setRuns] = useState<EvalRun[]>([])
  const [version, setVersion] = useState(0)
  const [loadedVersion, setLoadedVersion] = useState(-1)

  useEffect(() => {
    const controller = new AbortController()
    api
      .getObservability(controller.signal)
      .then((current) => {
        setOverview(current)
        setError(null)
        setLocked(false)
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return
        setError(message(reason))
        setLocked(reason instanceof ApiError && reason.status === 401)
      })
    api
      .listEvalRuns(controller.signal)
      .then(setRuns)
      .catch(() => {
        if (!controller.signal.aborted) setRuns([])
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadedVersion(version)
      })
    return () => controller.abort()
  }, [version])

  return {
    overview,
    runs,
    error,
    locked,
    loading: loadedVersion !== version,
    refresh: () => setVersion((current) => current + 1),
  }
}
