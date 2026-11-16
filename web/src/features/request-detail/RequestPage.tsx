import { ArrowLeft, Globe, Wallet } from 'lucide-react'
import { useRef, useState } from 'react'
import { Link, useParams } from 'react-router'

import type { Preferences, ShoppingRequest } from '../../api/types'
import { NewRequestButton } from '../../components/NewRequestButton'
import { PageHeader } from '../../components/PageHeader'
import { StatusBadge } from '../../components/StatusBadge'
import { budgetLabel, countryName, timeAgo } from '../../lib/format'
import { DeleteRequestButton } from './DeleteRequestButton'
import { KpiStrip } from './KpiStrip'
import { PriceComparator } from './PriceComparator'
import { RequestFailed, RequestNotice, RequestProgress } from './RequestStatusCards'
import { RequestSummary } from './RequestSummary'
import { ShoppingPlanCard } from './ShoppingPlanCard'
import { useShoppingRequest } from './useShoppingRequest'

const PREFERENCE_LABELS: Record<keyof Preferences, string> = {
  brands: 'Brands',
  colors: 'Colors',
  materials: 'Materials',
  payment: 'Payment',
  notes: 'Other',
}

function RequestFacts({ request }: { request: ShoppingRequest }) {
  const chip = 'inline-flex items-center gap-1 rounded-full bg-white/40 px-2.5 py-1 text-[11px]'
  const preferences = (Object.keys(PREFERENCE_LABELS) as (keyof Preferences)[]).flatMap((field) => {
    const value = request.preferences[field]
    return value ? [{ label: PREFERENCE_LABELS[field], value }] : []
  })

  return (
    <ul className="flex flex-wrap gap-1.5">
      <li className={chip}>
        <Globe className="size-3 text-muted" /> {countryName(request.market.country)}
      </li>
      <li className={chip}>
        <Wallet className="size-3 text-muted" /> {budgetLabel(request.budget, request.market.currency)}
      </li>
      {preferences.map(({ label, value }) => (
        <li key={label} className={chip}>
          <span className="text-muted">{label}:</span> {value}
        </li>
      ))}
    </ul>
  )
}

export function RequestPage() {
  const { requestId = '' } = useParams()
  return <RequestScreen key={requestId} requestId={requestId} />
}

function RequestScreen({ requestId }: { requestId: string }) {
  const { request, error } = useShoppingRequest(requestId)
  const [pickedId, setPickedId] = useState<string | null>(null)
  const comparatorRef = useRef<HTMLDivElement>(null)

  function selectProduct(productId: string) {
    setPickedId(productId)
    if (window.matchMedia('(max-width: 1023px)').matches) {
      comparatorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const back = (
    <Link to="/requests" className="inline-flex items-center gap-1 hover:text-blush">
      <ArrowLeft className="size-3" /> All requests
    </Link>
  )

  if (!request) {
    return (
      <div className="mx-auto max-w-none space-y-5">
        <PageHeader title="Shopping request" eyebrow={back} />
        <RequestNotice message={error ?? 'Loading the shopping request...'} />
      </div>
    )
  }

  const plan = request.status === 'done' ? request.plan : null
  const selectedId = pickedId ?? plan?.items[0]?.product.id ?? null
  const selected = plan?.items.find((item) => item.product.id === selectedId) ?? null

  return (
    <div className="mx-auto max-w-none space-y-5">
      <PageHeader
        title="Shopping request"
        eyebrow={back}
        subtitle={
          <span className="flex items-center gap-2">
            <StatusBadge status={request.status} /> sent {timeAgo(request.created_at)}
          </span>
        }
        actions={
          <>
            <DeleteRequestButton requestId={request.id} status={request.status} />
            <NewRequestButton />
          </>
        }
      />

      <div className="grid items-stretch gap-5 2xl:grid-cols-[minmax(0,1fr)_minmax(0,1.25fr)]">
        <section className="glass space-y-3 p-4">
          <p className="text-sm leading-relaxed">{request.description}</p>
          <RequestFacts request={request} />
        </section>
        {plan && <KpiStrip plan={plan} />}
      </div>

      {error && <RequestNotice message={error} />}
      {request.status === 'failed' && <RequestFailed request={request} />}
      {(request.status === 'queued' || request.status === 'running') && <RequestProgress request={request} />}

      {plan && (
        <>
          <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.7fr)_minmax(280px,1fr)] 2xl:grid-cols-[minmax(0,2.4fr)_minmax(340px,1fr)]">
            <ShoppingPlanCard plan={plan} selectedId={selectedId} onSelect={selectProduct} />
            <div className="space-y-5 lg:sticky lg:top-0">
              <div ref={comparatorRef} className="scroll-mt-4">
                <PriceComparator item={selected} currency={plan.market.currency} />
              </div>
              <RequestSummary request={request} plan={plan} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
