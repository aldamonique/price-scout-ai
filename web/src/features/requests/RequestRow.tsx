import { ChevronRight, Globe } from 'lucide-react'
import { Link } from 'react-router'

import type { RequestSummary } from '../../api/types'
import { StatusBadge } from '../../components/StatusBadge'
import { budgetLabel, countryName, money, timeAgo } from '../../lib/format'

export function RequestRow({ request }: { request: RequestSummary }) {
  const { currency } = request.market

  return (
    <Link
      to={`/requests/${request.id}`}
      className="glass group flex items-center gap-4 rounded-2xl! px-4 py-3 transition hover:bg-white/45"
    >
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex flex-wrap items-center gap-2">
          <StatusBadge status={request.status} />
          <span className="text-[11px] text-muted">{timeAgo(request.created_at)}</span>
        </div>
        <p className="line-clamp-2 text-sm">{request.description}</p>
        <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px] text-muted">
          <span className="inline-flex items-center gap-1">
            <Globe className="size-3" /> {countryName(request.market.country)}
          </span>
          <span>{budgetLabel(request.budget, currency)}</span>
        </p>
      </div>

      <div className="hidden shrink-0 text-right sm:block">
        {request.total != null ? (
          <>
            <p className="text-sm font-semibold">{money(request.total, currency)}</p>
            <p className="text-[11px] text-muted">
              {request.item_count} {request.item_count === 1 ? 'item' : 'items'}
            </p>
          </>
        ) : (
          <p className="text-[11px] text-muted">no plan yet</p>
        )}
      </div>

      <ChevronRight className="size-4 shrink-0 text-muted transition group-hover:translate-x-0.5 group-hover:text-blush" />
    </Link>
  )
}
