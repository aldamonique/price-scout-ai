import { CircleAlert, CircleCheck } from 'lucide-react'

import type { ShoppingPlan } from '../../api/types'
import { money } from '../../lib/format'

export function BudgetBar({ plan }: { plan: ShoppingPlan }) {
  const { currency } = plan.market

  if (plan.budget == null || plan.leftover == null) {
    return (
      <p className="mb-4 text-sm">
        <span className="font-semibold">{money(plan.total, currency)}</span>
        <span className="text-muted"> in total · no budget set</span>
      </p>
    )
  }

  const used = plan.budget > 0 ? Math.min(plan.total / plan.budget, 1) * 100 : 0
  const over = plan.leftover < 0

  return (
    <div className="mb-4">
      <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm">
          <span className="font-semibold">{money(plan.total, currency)}</span>
          <span className="text-muted"> of {money(plan.budget, currency)}</span>
        </p>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs ${
            over ? 'bg-blush-soft text-blush' : 'bg-mint-soft text-mint'
          }`}
        >
          {over ? <CircleAlert className="size-3.5" /> : <CircleCheck className="size-3.5" />}
          {over ? `${money(-plan.leftover, currency)} over` : `${money(plan.leftover, currency)} left`}
        </span>
      </div>
      <div
        role="progressbar"
        aria-label="Budget used"
        aria-valuenow={Math.round(used)}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-2 overflow-hidden rounded-full bg-white/50"
      >
        <div className="h-full rounded-full bg-leaf/70" style={{ width: `${used}%` }} />
      </div>
    </div>
  )
}
