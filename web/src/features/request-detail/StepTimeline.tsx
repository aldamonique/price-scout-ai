import { Check, Clock, LoaderCircle, TriangleAlert } from 'lucide-react'

import type { AgentStep, AgentUsage } from '../../api/types'
import { integer, seconds, usd } from '../../lib/format'
import { STEP_META } from './stepMeta'

interface StepTimelineProps {
  steps: AgentStep[]
  working?: boolean
  durationMs?: number
  usage?: Pick<AgentUsage, 'input_tokens' | 'output_tokens' | 'cost_usd'>
}

export function StepTimeline({ steps, working = false, durationMs, usage }: StepTimelineProps) {
  return (
    <div>
      <ol className="relative space-y-1.5 before:absolute before:top-3 before:bottom-3 before:left-[11px] before:w-px before:bg-lilac/30">
        {steps.map((step) => {
          const meta = STEP_META[step.kind]
          const Icon = meta.icon
          const highlighted = step.kind === 'replan' || !step.ok
          return (
            <li
              key={step.number}
              className={`relative flex gap-2.5 rounded-2xl p-1.5 ${highlighted ? 'bg-amber-soft/80' : ''}`}
            >
              <span
                className={`z-10 grid size-6 shrink-0 place-items-center rounded-full text-white ${
                  !step.ok ? 'bg-blush' : highlighted ? 'bg-amber' : 'bg-mint'
                }`}
              >
                {step.ok ? <Check className="size-3.5" strokeWidth={3} /> : <TriangleAlert className="size-3.5" />}
              </span>
              <span className="grid size-8 shrink-0 place-items-center rounded-xl bg-white/50">
                <Icon className={`size-3.5 ${highlighted ? 'text-amber' : 'text-muted'}`} />
              </span>
              <div className="min-w-0">
                <p className={`text-xs font-semibold ${highlighted ? 'text-amber' : ''}`}>{meta.title}</p>
                <p className="text-[11px] break-words text-muted">{step.summary}</p>
                <p className="text-[11px] text-muted/80">
                  {step.tool} · {seconds(step.duration_ms)}
                </p>
              </div>
            </li>
          )
        })}

        {working && (
          <li className="relative flex items-center gap-2.5 p-1.5 text-xs text-muted">
            <span className="z-10 grid size-6 place-items-center rounded-full bg-white">
              <LoaderCircle className="size-3.5 animate-spin text-blush" />
            </span>
            {steps.length === 0 ? 'Reading the request...' : 'Deciding the next step...'}
          </li>
        )}
      </ol>

      {usage && durationMs !== undefined && (
        <p className="mt-3 flex items-center gap-1.5 border-t border-white/70 pt-2.5 text-[11px] text-muted">
          <Clock className="size-3.5" />
          {steps.length} steps · {seconds(durationMs)} · {integer(usage.input_tokens + usage.output_tokens)} tokens ·{' '}
          {usd(usage.cost_usd)}
        </p>
      )}
    </div>
  )
}
