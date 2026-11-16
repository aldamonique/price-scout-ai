import { Check, TriangleAlert } from 'lucide-react'

import type { LlmCall } from '../../api/types'
import { duration, integer, usd } from '../../lib/format'
import { useRequestCalls } from './useRequestCalls'

export function CallList({ calls }: { calls: LlmCall[] }) {
  const slowest = Math.max(...calls.map((call) => call.latency_ms), 1)

  return (
    <ol className="space-y-1.5">
      {calls.map((call, index) => (
        <li key={call.id} className="rounded-xl bg-white/30 px-2.5 py-2">
          <div className="flex items-center gap-2 text-[11px]">
            <span className="w-5 shrink-0 text-muted">{index + 1}</span>
            <span
              className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                call.task === 'agent' ? 'bg-leaf-soft text-leaf-deep' : 'bg-white/70 text-ink'
              }`}
            >
              {call.task}
            </span>
            <span className="min-w-0 flex-1 truncate text-muted">
              {call.model} · {call.prompt_version}
            </span>
            {call.ok ? (
              <Check className="size-3.5 shrink-0 text-mint" aria-label="ok" />
            ) : (
              <TriangleAlert className="size-3.5 shrink-0 text-amber" aria-label="failed" />
            )}
          </div>
          <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-white/60" aria-hidden>
            <div className="h-full rounded-full bg-leaf/70" style={{ width: `${(call.latency_ms / slowest) * 100}%` }} />
          </div>
          <p className="mt-1 text-[10px] text-muted">
            {duration(call.latency_ms)} · {integer(call.input_tokens)} in / {integer(call.output_tokens)} out ·{' '}
            {call.cost_usd == null ? 'no price' : usd(call.cost_usd)}
          </p>
          {call.error && <p className="mt-1 text-[10px] text-amber">{call.error}</p>}
        </li>
      ))}
    </ol>
  )
}

export function CallTrace({ requestId }: { requestId: string }) {
  const { calls, error } = useRequestCalls(requestId)

  return (
    <div className="mt-3">
      <h3 className="mb-2 text-xs font-semibold">Model calls</h3>
      {error && <p className="text-[11px] text-muted">{error}</p>}
      {!calls && !error && <p className="text-[11px] text-muted">Loading...</p>}
      {calls && calls.length === 0 && (
        <p className="text-[11px] text-muted">No calls recorded for this request.</p>
      )}
      {calls && calls.length > 0 && <CallList calls={calls} />}
    </div>
  )
}
