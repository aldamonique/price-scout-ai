import { CircleAlert, CircleCheck, Sparkles } from 'lucide-react'
import { useState } from 'react'

import type { ShoppingPlan, ShoppingRequest } from '../../api/types'
import { GlassCard } from '../../components/GlassCard'
import { integer, seconds, usd } from '../../lib/format'
import { CallTrace } from './CallTrace'
import { StepTimeline } from './StepTimeline'

const VIEWS = [
  { id: 'insights', label: 'Insights' },
  { id: 'steps', label: 'Agent steps' },
  { id: 'run', label: 'Run details' },
] as const

type View = (typeof VIEWS)[number]['id']

function Insights({ plan }: { plan: ShoppingPlan }) {
  const withinBudget = plan.budget == null || plan.total <= plan.budget
  const complete = withinBudget && plan.unmet.length === 0
  return (
    <div className="space-y-2">
      <div className={`flex items-center gap-2.5 rounded-2xl p-3 ${complete ? 'bg-mint-soft/70' : 'bg-amber-soft/70'}`}>
        {complete ? <CircleCheck className="size-5 shrink-0 text-mint" /> : <CircleAlert className="size-5 shrink-0 text-amber" />}
        <div>
          <p className="text-xs font-semibold">{complete ? 'Plan ready' : 'Partial plan'}</p>
          <p className="text-[11px] text-muted">
            {complete
              ? plan.budget == null
                ? 'Every item was found.'
                : 'Everything fits the budget.'
              : withinBudget
                ? 'Some items were not found.'
                : 'The plan goes over the budget.'}
          </p>
        </div>
      </div>
      <ul className="space-y-1.5">
        {plan.insights.map((insight) => (
          <li key={insight} className="rounded-xl bg-white/30 px-3 py-2 text-xs">
            {insight}
          </li>
        ))}
        {plan.unmet.length > 0 && (
          <li className="rounded-xl bg-amber-soft/60 px-3 py-2 text-xs">Not found: {plan.unmet.join(', ')}.</li>
        )}
      </ul>
    </div>
  )
}

function RunDetails({ plan, request, durationMs }: { plan: ShoppingPlan; request: ShoppingRequest; durationMs: number }) {
  const { usage, stats } = plan
  const rows = [
    ['Model', usage.agent_model ?? '—'],
    ['Prompt version', usage.agent_prompt_version ?? '—'],
    ['Steps', integer(request.steps.length)],
    ['Duration', seconds(Math.max(durationMs, 0))],
    ['Searches', integer(stats.searches)],
    ['Listings / discarded', `${integer(stats.listings)} / ${integer(stats.discarded)}`],
    ['Tokens in / out', `${integer(usage.input_tokens)} / ${integer(usage.output_tokens)}`],
    ['Cost', usd(usage.cost_usd)],
  ]
  return (
    <>
      <dl className="grid grid-cols-2 gap-1.5">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-xl bg-white/30 px-2.5 py-1.5">
            <dt className="text-[10px] text-muted">{label}</dt>
            <dd className="truncate text-xs font-medium" title={value}>
              {value}
            </dd>
          </div>
        ))}
      </dl>
      <CallTrace requestId={request.id} />
    </>
  )
}

export function RequestSummary({ request, plan }: { request: ShoppingRequest; plan: ShoppingPlan }) {
  const [view, setView] = useState<View>('insights')
  const durationMs = Date.parse(request.updated_at) - Date.parse(request.created_at)

  return (
    <GlassCard title="Request summary" icon={Sparkles}>
      <div role="tablist" className="mb-3 grid grid-cols-3 gap-1 rounded-full bg-white/25 p-1 text-[11px]">
        {VIEWS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={view === id}
            onClick={() => setView(id)}
            className={`rounded-full py-1.5 transition ${
              view === id ? 'bg-white/70 font-semibold text-blush' : 'text-muted hover:text-ink'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {view === 'insights' && <Insights plan={plan} />}
      {view === 'steps' && <StepTimeline steps={request.steps} durationMs={durationMs} usage={plan.usage} />}
      {view === 'run' && <RunDetails plan={plan} request={request} durationMs={durationMs} />}
    </GlassCard>
  )
}
