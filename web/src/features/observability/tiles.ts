import { CircleCheck, Coins, Cpu, Timer, TriangleAlert, Zap, type LucideIcon } from 'lucide-react'

import type { Overview } from '../../api/types'
import { compact, duration, integer, percent, seconds, usd } from '../../lib/format'

export interface Tile {
  label: string
  value: string
  hint: string
  icon: LucideIcon
  highlight?: boolean
}

export function overviewTiles({ runs, llm }: Overview): Tile[] {
  return [
    {
      label: 'Total cost',
      value: llm.cost_usd == null ? '—' : usd(llm.cost_usd),
      hint:
        runs.avg_cost_usd == null ? 'no finished request yet' : `${usd(runs.avg_cost_usd)} per request`,
      icon: Coins,
      highlight: true,
    },
    {
      label: 'Success rate',
      value: percent(runs.success_rate),
      hint: `${integer(runs.done)} done · ${integer(runs.failed)} failed · ${integer(runs.in_progress)} running`,
      icon: CircleCheck,
    },
    {
      label: 'Request duration',
      value: runs.avg_duration_s == null ? '—' : seconds(runs.avg_duration_s * 1000),
      hint: runs.p95_duration_s == null ? 'average' : `p95 ${seconds(runs.p95_duration_s * 1000)}`,
      icon: Timer,
    },
    {
      label: 'Model calls',
      value: integer(llm.calls),
      hint: `avg latency ${duration(llm.avg_latency_ms)}`,
      icon: Zap,
    },
    {
      label: 'Tokens',
      value: compact(llm.input_tokens + llm.output_tokens),
      hint: `${compact(llm.input_tokens)} in · ${compact(llm.output_tokens)} out`,
      icon: Cpu,
    },
    {
      label: 'Call error rate',
      value: percent(llm.error_rate),
      hint: llm.unpriced_calls > 0 ? `${integer(llm.unpriced_calls)} calls without a price` : 'every call priced',
      icon: TriangleAlert,
    },
  ]
}
