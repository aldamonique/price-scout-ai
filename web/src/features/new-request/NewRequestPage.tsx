import { useState } from 'react'
import { Link } from 'react-router'

import { GlassCard } from '../../components/GlassCard'
import { PageHeader } from '../../components/PageHeader'
import { StatusBadge } from '../../components/StatusBadge'
import { budgetLabel, money, timeAgo } from '../../lib/format'
import { useRequestHistory } from '../../hooks/useRequestHistory'
import { EMPTY_DRAFT, toRequestBody } from './draft'
import { RequestComposer } from './RequestComposer'
import { useMarkets, useSubmitRequest } from './useSubmitRequest'

const STEPS = [
  { title: 'Plans the budget', text: 'Splits it between the items you asked for.' },
  { title: 'Searches the stores', text: 'Google Shopping in your country, every item at once.' },
  { title: 'Checks the details', text: 'Size, capacity, dose and flavor as you asked; drops accessories.' },
  { title: 'Compares prices', text: 'Finds the cheapest store for each product.' },
]

function HowItWorks() {
  return (
    <GlassCard title="How the agent works" subtitle="Four steps to a better fit">
      <ol className="grid gap-2 sm:grid-cols-2">
        {STEPS.map(({ title, text }, index) => (
          <li key={title} className="step-card min-h-28 rounded-2xl p-3.5">
            <span className="mb-2 inline-flex rounded-full border border-white/80 bg-white/50 px-2 py-1 text-[9px] font-semibold tracking-[0.12em] text-muted shadow-[inset_0_1px_0_rgb(255_255_255/.9)]">
              0{index + 1}
            </span>
            <div>
              <p className="text-[11px] font-semibold leading-snug sm:text-xs">{title}</p>
              <p className="mt-1 text-[10px] leading-relaxed text-muted sm:text-[11px]">{text}</p>
            </div>
          </li>
        ))}
      </ol>
    </GlassCard>
  )
}

function RecentRequests() {
  const { requests } = useRequestHistory()
  const recent = requests?.slice(0, 4) ?? []

  return (
    <GlassCard
      title="Recent requests"
      action={
        <Link to="/requests" className="text-[11px] font-medium text-blush hover:underline">
          See all
        </Link>
      }
    >
      {recent.length === 0 ? (
        <p className="text-xs text-muted">{requests ? 'Your requests will appear here.' : 'Loading...'}</p>
      ) : (
        <ul className="space-y-1.5">
          {recent.map((request) => (
            <li key={request.id}>
              <Link
                to={`/requests/${request.id}`}
                className="block rounded-xl bg-white/25 px-3 py-2 transition hover:bg-white/50"
              >
                <div className="flex items-center justify-between gap-2">
                  <StatusBadge status={request.status} />
                  <span className="text-[10px] text-muted">{timeAgo(request.created_at)}</span>
                </div>
                <p className="mt-1 truncate text-xs">{request.description}</p>
                <p className="text-[10px] text-muted">
                  {request.total != null
                    ? `${money(request.total, request.market.currency)} · ${budgetLabel(request.budget, request.market.currency)}`
                    : budgetLabel(request.budget, request.market.currency)}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </GlassCard>
  )
}

export function NewRequestPage() {
  const [draft, setDraft] = useState(EMPTY_DRAFT)
  const { markets, error: marketsError } = useMarkets()
  const { submit, submitting, error } = useSubmitRequest()

  return (
    <div className="mx-auto max-w-[1640px] space-y-6 sm:space-y-7">
      <PageHeader
        title="New request"
        subtitle="Tell the agent what you want to buy: furniture, tech, books, food, supplements, pharmacy. It searches the stores and compares prices."
      />

      <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-4 sm:gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(310px,0.85fr)] xl:gap-6">
        <RequestComposer
          draft={draft}
          markets={markets}
          submitting={submitting}
          error={error ? `Could not send the request: ${error}` : marketsError}
          onChange={setDraft}
          onSubmit={() => void submit(toRequestBody(draft))}
        />
        <div className="space-y-4">
          <HowItWorks />
          <RecentRequests />
        </div>
      </div>
    </div>
  )
}
