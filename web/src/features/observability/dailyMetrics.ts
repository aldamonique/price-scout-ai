import type { DailyUsage } from '../../api/types'
import { compact, integer, usd } from '../../lib/format'

export const METRICS = [
  { id: 'cost', label: 'Cost', value: (day: DailyUsage) => day.cost_usd ?? 0, format: (v: number) => usd(v) },
  {
    id: 'tokens',
    label: 'Tokens',
    value: (day: DailyUsage) => day.input_tokens + day.output_tokens,
    format: (v: number) => compact(v),
  },
  { id: 'calls', label: 'Calls', value: (day: DailyUsage) => day.calls, format: (v: number) => integer(v) },
] as const

export type MetricId = (typeof METRICS)[number]['id']
