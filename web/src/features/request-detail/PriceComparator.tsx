import { ExternalLink, Scale, Sparkles } from 'lucide-react'

import type { PlanItem } from '../../api/types'
import { GlassCard } from '../../components/GlassCard'
import { StoreBadge } from '../../components/StoreBadge'
import { installments, money } from '../../lib/format'

interface PriceComparatorProps {
  item: PlanItem | null
  currency: string
}

export function PriceComparator({ item, currency }: PriceComparatorProps) {
  return (
    <GlassCard title="Price comparison" subtitle={item?.product.name} icon={Scale}>
      {item ? (
        <ul className="space-y-2">
          {item.product.offers.map((offer, index) => {
            const split = installments(offer.installment_months, offer.installment_amount, currency)
            return (
              <li key={offer.store}>
                <a
                  href={offer.url ?? undefined}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2.5 rounded-xl bg-white/40 p-2.5 transition hover:bg-white/60"
                >
                  <StoreBadge store={offer.store} icon={offer.store_icon} size="sm" />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[11px] text-muted" title={offer.store}>
                      {offer.store}
                    </span>
                    <span className="flex flex-wrap items-center gap-x-2">
                      <span className="text-sm font-semibold">{money(offer.price, currency)}</span>
                      {index === 0 && (
                        <span className="rounded-full bg-mint-soft px-2 text-[10px] whitespace-nowrap text-mint">
                          Lowest price
                        </span>
                      )}
                    </span>
                    {split && <span className="block text-[11px] text-muted">or {split}</span>}
                  </span>
                  <ExternalLink className="size-3.5 shrink-0 text-muted" />
                </a>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="text-xs text-muted">Select an item of the plan to compare stores.</p>
      )}

      {item && item.savings > 0 && (
        <div className="mt-3 flex items-center justify-between rounded-2xl bg-mint-soft px-3 py-2.5">
          <span className="flex items-center gap-1.5 text-xs">
            <Sparkles className="size-3.5 text-mint" /> Save up to
          </span>
          <span className="text-sm font-semibold text-mint">{money(item.savings, currency)}</span>
        </div>
      )}
    </GlassCard>
  )
}
