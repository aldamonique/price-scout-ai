import { useState } from 'react'

import type { DailyUsage } from '../../api/types'
import { integer } from '../../lib/format'
import { METRICS, type MetricId } from './dailyMetrics'

const dayLabel = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })

function label(day: string): string {
  return dayLabel.format(new Date(`${day}T00:00:00Z`))
}

export function DailyUsageChart({ daily }: { daily: DailyUsage[] }) {
  const [metricId, setMetricId] = useState<MetricId>('cost')
  const [hovered, setHovered] = useState<number | null>(null)
  const metric = METRICS.find((m) => m.id === metricId) ?? METRICS[0]
  const values = daily.map(metric.value)
  const max = Math.max(...values, 0)

  return (
    <section className="glass flex min-w-0 flex-col gap-4 p-4 sm:p-5">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold">Model usage per day</h2>
          <p className="text-[11px] text-muted">Agent and judge calls, last {daily.length} days with activity</p>
        </div>
        <div role="tablist" aria-label="Metric" className="flex gap-1 rounded-full bg-white/40 p-1">
          {METRICS.map(({ id, label: name }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={metricId === id}
              onClick={() => setMetricId(id)}
              className={`rounded-full px-3 py-1 text-[11px] transition ${
                metricId === id ? 'bg-white font-semibold text-ink' : 'text-muted hover:text-ink'
              }`}
            >
              {name}
            </button>
          ))}
        </div>
      </header>

      {daily.length === 0 ? (
        <p className="py-10 text-center text-xs text-muted">No model calls yet. Run a shopping request to see usage.</p>
      ) : (
        <div className="relative">
          <div className="pointer-events-none absolute inset-x-0 top-11 flex justify-between border-b border-dashed border-ink/10 pb-1 text-[10px] text-muted">
            <span>{metric.format(max)}</span>
          </div>
          <ol className="flex h-52 items-end gap-0.5 border-b border-ink/15 pt-16" aria-label={`${metric.label} per day`}>
            {daily.map((day, index) => {
              const value = values[index] ?? 0
              const height = max > 0 ? Math.max((value / max) * 100, value > 0 ? 2 : 0) : 0
              return (
                <li
                  key={day.day}
                  className="relative flex h-full min-w-0 flex-1 items-end justify-center"
                  onMouseEnter={() => setHovered(index)}
                  onMouseLeave={() => setHovered(null)}
                  onFocus={() => setHovered(index)}
                  onBlur={() => setHovered(null)}
                  tabIndex={0}
                  aria-label={`${label(day.day)}: ${metric.format(value)}`}
                >
                  <span
                    className={`w-full max-w-10 rounded-t-[4px] transition ${hovered === index ? 'bg-leaf-deep' : 'bg-leaf'}`}
                    style={{ height: `${height}%` }}
                  />
                  {hovered === index && (
                    <span
                      role="tooltip"
                      className="absolute bottom-full z-10 mb-1 rounded-lg bg-ink px-2.5 py-1.5 text-[11px] whitespace-nowrap text-white shadow-lg"
                    >
                      <span className="block text-white/70">{label(day.day)}</span>
                      <span className="font-semibold">{metric.format(value)}</span>
                      <span className="block text-white/70">{integer(day.calls)} calls</span>
                    </span>
                  )}
                </li>
              )
            })}
          </ol>
          <ol className="mt-1.5 flex gap-0.5 text-[10px] text-muted" aria-hidden>
            {daily.map((day, index) => (
              <li key={day.day} className="min-w-0 flex-1 truncate text-center">
                {index === 0 || index === daily.length - 1 || daily.length <= 7 ? label(day.day) : ''}
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  )
}
