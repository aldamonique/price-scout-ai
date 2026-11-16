import { KeyRound } from 'lucide-react'
import { useState, type FormEvent } from 'react'

import { saveAdminToken } from '../../lib/adminToken'

export function AdminTokenForm({ onSaved }: { onSaved: () => void }) {
  const [token, setToken] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    saveAdminToken(token)
    onSaved()
  }

  return (
    <form onSubmit={handleSubmit} className="glass flex flex-wrap items-end gap-3 p-4 sm:p-5">
      <div className="min-w-56 flex-1">
        <label htmlFor="admin-token" className="mb-1 flex items-center gap-1.5 text-xs font-semibold">
          <KeyRound className="size-3.5" /> Admin token
        </label>
        <p className="mb-2 text-[11px] text-muted">
          This demo protects observability and deleting requests. The token is the ADMIN_TOKEN set on the API.
        </p>
        <input
          id="admin-token"
          type="password"
          value={token}
          onChange={(event) => setToken(event.target.value)}
          autoComplete="off"
          className="field"
        />
      </div>
      <button type="submit" className="primary-action rounded-full px-5 py-2.5 text-xs font-semibold transition">
        Unlock
      </button>
    </form>
  )
}
