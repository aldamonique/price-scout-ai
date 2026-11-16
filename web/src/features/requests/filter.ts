import type { RequestStatus, RequestSummary } from '../../api/types'
import { countryName } from '../../lib/format'

export type StatusFilter = 'all' | RequestStatus

export const STATUS_FILTERS: { id: StatusFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'done', label: 'Done' },
  { id: 'running', label: 'Running' },
  { id: 'failed', label: 'Failed' },
]

function matchesStatus(request: RequestSummary, status: StatusFilter): boolean {
  if (status === 'all') return true
  if (status === 'running') return request.status === 'running' || request.status === 'queued'
  return request.status === status
}

function matchesText(request: RequestSummary, query: string): boolean {
  const haystack = `${request.description} ${countryName(request.market.country)}`.toLowerCase()
  return query
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean)
    .every((word) => haystack.includes(word))
}

export function filterRequests(requests: RequestSummary[], query: string, status: StatusFilter): RequestSummary[] {
  return requests.filter((r) => matchesStatus(r, status) && matchesText(r, query))
}

export function countByStatus(requests: RequestSummary[], status: StatusFilter): number {
  return requests.filter((r) => matchesStatus(r, status)).length
}
