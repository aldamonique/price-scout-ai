import { CalendarRange, ChartColumn, RefreshCw, Ruler, Search, type LucideIcon } from 'lucide-react'

import type { StepKind } from '../../api/types'

export const STEP_META: Record<StepKind, { title: string; icon: LucideIcon }> = {
  plan: { title: 'Planned the budget', icon: CalendarRange },
  replan: { title: 'Re-planned', icon: RefreshCw },
  search: { title: 'Searched offers', icon: Search },
  measure: { title: 'Checked the size', icon: Ruler },
  metrics: { title: 'Looked up prices', icon: ChartColumn },
}
