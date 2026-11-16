import { FlaskConical } from 'lucide-react'

import type { EvalRun } from '../../api/types'
import { percent, timeAgo, usd } from '../../lib/format'
import { glossaryEffect } from './glossaryEffect'

function points(after: number, before: number): string {
  const delta = Math.round((after - before) * 1000) / 10
  return `${delta >= 0 ? '+' : ''}${delta} pts`
}

export function JudgeAccuracy({ runs }: { runs: EvalRun[] }) {
  const effect = glossaryEffect(runs)

  return (
    <section className="glass min-w-0 p-4 sm:p-5">
      <header className="mb-3 flex items-start gap-2.5">
        <FlaskConical className="mt-0.5 size-4 text-leaf" />
        <div>
          <h2 className="text-sm font-semibold">Judge accuracy</h2>
          <p className="text-[11px] text-muted">
            Labeled listings: does the judge discard the right ones and group the same product across stores?
          </p>
        </div>
      </header>

      {runs.length === 0 ? (
        <p className="rounded-xl bg-white/40 px-3 py-2.5 text-xs text-muted">
          No evaluation yet. Run <code>uv run python -m evals.run</code> in api/.
        </p>
      ) : (
        <>
          {effect && (
            <div className="leaf-card mb-3 grid gap-3 rounded-2xl! p-3.5 sm:grid-cols-3">
              <div>
                <p className="text-[11px] text-white/80">Glossary effect on decisions</p>
                <p className="text-xl font-semibold">
                  {points(effect.with.decision_accuracy, effect.without.decision_accuracy)}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-white/80">On discard F1</p>
                <p className="text-xl font-semibold">{points(effect.with.discard.f1, effect.without.discard.f1)}</p>
              </div>
              <div>
                <p className="text-[11px] text-white/80">On grouping F1</p>
                <p className="text-xl font-semibold">{points(effect.with.grouping.f1, effect.without.grouping.f1)}</p>
              </div>
            </div>
          )}
          <div className="-mx-1 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-xs">
              <thead>
                <tr className="text-[10px] tracking-wide text-muted uppercase">
                  <th className="px-1 pb-2 font-medium">Run</th>
                  <th className="px-1 pb-2 text-right font-medium">Decisions</th>
                  <th className="px-1 pb-2 text-right font-medium">Discard F1</th>
                  <th className="px-1 pb-2 text-right font-medium">Grouping F1</th>
                  <th className="px-1 pb-2 text-right font-medium">Cases</th>
                  <th className="px-1 pb-2 text-right font-medium">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/60">
                {runs.map((run) => (
                  <tr key={run.run_id}>
                    <td className="px-1 py-2">
                      <span
                        className={`mr-1.5 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                          run.glossary ? 'bg-leaf-soft text-leaf-deep' : 'bg-white/70 text-ink'
                        }`}
                      >
                        {run.glossary ? 'glossary' : 'no glossary'}
                      </span>
                      {run.judge_model} · {run.prompt_version}
                      <span className="ml-1.5 text-muted">{timeAgo(run.created_at)}</span>
                    </td>
                    <td className="px-1 py-2 text-right">{percent(run.decision_accuracy)}</td>
                    <td className="px-1 py-2 text-right">{run.discard.f1.toFixed(2)}</td>
                    <td className="px-1 py-2 text-right">{run.grouping.f1.toFixed(2)}</td>
                    <td className="px-1 py-2 text-right">
                      {run.cases}
                      {run.failed_cases > 0 && (
                        <span className="ml-1 rounded-full bg-amber-soft px-1.5 py-0.5 text-[10px] font-semibold text-amber">
                          {run.failed_cases} failed
                        </span>
                      )}
                    </td>
                    <td className="px-1 py-2 text-right">{run.cost_usd == null ? '—' : usd(run.cost_usd)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  )
}
