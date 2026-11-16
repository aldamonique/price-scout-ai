import { Globe, Package } from 'lucide-react'

import type { ShoppingPlan } from '../../api/types'
import { GlassCard } from '../../components/GlassCard'
import { countryName } from '../../lib/format'
import { BudgetBar } from './BudgetBar'
import { PlanItemCard } from './PlanItemCard'

interface ShoppingPlanCardProps {
  plan: ShoppingPlan
  selectedId: string | null
  onSelect: (productId: string) => void
}

export function ShoppingPlanCard({ plan, selectedId, onSelect }: ShoppingPlanCardProps) {
  const { currency, country } = plan.market

  return (
    <GlassCard
      title="Shopping plan"
      icon={Package}
      action={
        <span className="inline-flex items-center gap-1 rounded-full bg-white/50 px-2.5 py-0.5 text-[11px] text-muted">
          <Globe className="size-3" /> {countryName(country)} · {currency}
        </span>
      }
    >
      <BudgetBar plan={plan} />

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {plan.items.map((item) => (
          <PlanItemCard
            key={item.product.id}
            item={item}
            currency={currency}
            selected={item.product.id === selectedId}
            onSelect={() => onSelect(item.product.id)}
          />
        ))}
        {plan.items.length === 0 && (
          <p className="rounded-2xl bg-white/40 p-4 text-xs text-muted col-span-full">
            The agent found no products for this request. Try a larger budget or describe the items differently.
          </p>
        )}
      </div>
    </GlassCard>
  )
}
