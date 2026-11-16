import { Search, SearchX } from 'lucide-react'
import { useState } from 'react'
import { useSearchParams } from 'react-router'

import { NewRequestButton } from '../../components/NewRequestButton'
import { PageHeader } from '../../components/PageHeader'
import { countByStatus, filterRequests, STATUS_FILTERS, type StatusFilter } from './filter'
import { RequestRow } from './RequestRow'
import { useRequestHistory } from '../../hooks/useRequestHistory'

export function RequestsPage() {
  const [params, setParams] = useSearchParams()
  const [status, setStatus] = useState<StatusFilter>('all')
  const { requests, error } = useRequestHistory()
  const query = params.get('q') ?? ''

  const visible = requests ? filterRequests(requests, query, status) : []

  function setQuery(text: string) {
    setParams(text ? { q: text } : {}, { replace: true })
  }

  return (
    <div className="mx-auto max-w-none space-y-5">
      <PageHeader
        title="Requests"
        subtitle="Every shopping request, newest first. Open one to see its plan and prices."
        actions={<NewRequestButton />}
      />

      <div className="flex flex-wrap items-center gap-3">
        <label className="relative min-w-56 flex-1">
          <span className="sr-only">Search</span>
          <Search className="pointer-events-none absolute top-1/2 left-3.5 size-3.5 -translate-y-1/2 text-muted" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by description or country..."
            className="field rounded-full! py-2! pl-9!"
          />
        </label>

        <div role="tablist" aria-label="Status" className="flex gap-1 rounded-full bg-white/30 p-1">
          {STATUS_FILTERS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={status === id}
              onClick={() => setStatus(id)}
              className={`rounded-full px-3 py-1 text-xs transition ${
                status === id ? 'bg-white/70 font-semibold text-blush' : 'text-muted hover:text-ink'
              }`}
            >
              {label}
              {requests && <span className="ml-1 text-[10px] opacity-70">{countByStatus(requests, id)}</span>}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="glass rounded-2xl! px-4 py-3 text-xs text-blush">{error}</p>}
      {!requests && !error && <p className="px-1 text-xs text-muted">Loading...</p>}

      {requests && visible.length > 0 && (
        <ul className="space-y-2.5">
          {visible.map((request) => (
            <li key={request.id}>
              <RequestRow request={request} />
            </li>
          ))}
        </ul>
      )}

      {requests && visible.length === 0 && (
        <div className="glass flex flex-col items-center gap-3 px-6 py-12 text-center">
          <SearchX className="size-6 text-muted" />
          <p className="text-sm">{requests.length === 0 ? 'No requests yet.' : 'No request matches the search.'}</p>
          <p className="text-xs text-muted">
            {requests.length === 0
              ? 'Describe what you need and the agent shops for you.'
              : 'Try other words or another status.'}
          </p>
          {requests.length === 0 && <NewRequestButton />}
        </div>
      )}
    </div>
  )
}
