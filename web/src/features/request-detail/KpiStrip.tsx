import { BadgePercent, Coins, ScanSearch, Store, type LucideIcon } from 'lucide-react'

import type { ShoppingPlan } from '../../api/types'
import { planKpis } from './kpis'

const ICONS: LucideIcon[] = [ScanSearch, Store, BadgePercent, Coins]
const TINTS = ['text-blush', 'text-lilac', 'text-mint', 'text-amber']
const HIGHLIGHT = 2

export function KpiStrip({ plan }: { plan: ShoppingPlan | null | undefined }) {
  return (
    <ul className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      {planKpis(plan).map((kpi, index) => {
        const Icon = ICONS[index] ?? ScanSearch
        const highlight = index === HIGHLIGHT
        return (
          <li
            key={kpi.label}
            className={`${highlight ? 'leaf-card' : 'glass'} flex min-w-0 items-center gap-2.5 rounded-2xl! px-3 py-2.5`}
          >
            <span className={`grid size-7 shrink-0 place-items-center rounded-lg ${highlight ? 'bg-white/20' : 'bg-white/60'}`}>
              <Icon className={`size-3.5 ${highlight ? 'text-white' : TINTS[index]}`} />
            </span>
            <div className="min-w-0">
              <p className={`truncate text-[11px] ${highlight ? 'text-white/80' : 'text-muted'}`}>{kpi.label}</p>
              <p className="text-sm font-semibold">{kpi.value}</p>
              <p className={`truncate text-[10px] ${highlight ? 'text-white/70' : 'text-muted/80'}`}>{kpi.hint}</p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
