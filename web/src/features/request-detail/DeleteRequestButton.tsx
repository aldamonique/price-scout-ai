import { LoaderCircle, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router'

import { api } from '../../api/client'
import type { RequestStatus } from '../../api/types'

interface DeleteRequestButtonProps {
  requestId: string
  status: RequestStatus
}

export function DeleteRequestButton({ requestId, status }: DeleteRequestButtonProps) {
  const navigate = useNavigate()
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const running = status === 'queued' || status === 'running'

  async function remove() {
    setDeleting(true)
    setError(null)
    try {
      await api.deleteRequest(requestId)
      navigate('/requests', { replace: true })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not delete the request.')
      setDeleting(false)
      setConfirming(false)
    }
  }

  if (confirming) {
    return (
      <div role="group" aria-label="Confirm delete" className="flex items-center gap-1.5 text-xs">
        <span className="text-muted">Delete this request?</span>
        <button
          type="button"
          onClick={() => void remove()}
          disabled={deleting}
          className="inline-flex items-center gap-1 rounded-full bg-blush px-3 py-1.5 font-semibold text-white transition hover:bg-blush/90"
        >
          {deleting && <LoaderCircle className="size-3.5 animate-spin" />}
          Delete
        </button>
        <button
          type="button"
          onClick={() => setConfirming(false)}
          disabled={deleting}
          className="rounded-full px-3 py-1.5 text-muted transition hover:text-ink"
        >
          Cancel
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={() => setConfirming(true)}
        disabled={running}
        title={running ? 'Wait for the request to finish before deleting it.' : undefined}
        className="glass inline-flex items-center gap-1.5 rounded-full! px-4 py-2 text-xs font-medium transition hover:bg-white/60 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Trash2 className="size-3.5" /> Delete
      </button>
      {error && (
        <p role="alert" className="text-[11px] text-blush">
          {error}
        </p>
      )}
    </div>
  )
}
