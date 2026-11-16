import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'

import { api } from '../../api/client'
import type { Market, ShoppingRequestBody } from '../../api/types'

export function useSubmitRequest() {
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(body: ShoppingRequestBody) {
    setSubmitting(true)
    setError(null)
    try {
      const created = await api.submitRequest(body)
      navigate(`/requests/${created.id}`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not send the request.')
    } finally {
      setSubmitting(false)
    }
  }

  return { submit, submitting, error }
}

export function useMarkets() {
  const [markets, setMarkets] = useState<Market[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    api
      .listMarkets(controller.signal)
      .then(setMarkets)
      .catch(() => {
        if (!controller.signal.aborted) setError('Could not load the countries. Is the API running?')
      })
    return () => controller.abort()
  }, [])

  return { markets, error }
}
