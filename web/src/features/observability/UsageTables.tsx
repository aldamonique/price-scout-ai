import type { ReactNode } from 'react'
import { Link } from 'react-router'

import type { FailedRun, StageStats, ToolStats, VersionStats } from '../../api/types'
import { compact, duration, integer, percent, timeAgo, usd } from '../../lib/format'

interface TableProps {
  title: string
  subtitle: string
  head: string[]
  minWidth: string
  children: ReactNode
}

function Table({ title, subtitle, head, minWidth, children }: TableProps) {
  return (
    <section className="glass min-w-0 p-4 sm:p-5">
      <h2 className="text-sm font-semibold">{title}</h2>
      <p className="mb-3 text-[11px] text-muted">{subtitle}</p>
      <div className="-mx-1 overflow-x-auto">
        <table className={`w-full ${minWidth} text-left text-xs`}>
          <thead>
            <tr className="text-[10px] tracking-wide text-muted uppercase">
              {head.map((cell, index) => (
                <th key={cell} className={`px-1 pb-2 font-medium ${index > 0 ? 'text-right' : ''}`}>
                  {cell}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/60">{children}</tbody>
        </table>
      </div>
    </section>
  )
}

function rate(failed: number, total: number): string {
  return percent(total > 0 ? failed / total : null)
}

export function VersionTable({ versions }: { versions: VersionStats[] }) {
  return (
    <Table
      title="Models and prompt versions"
      subtitle="Compare versions before changing AGENT__PROMPT_VERSION or JUDGE__PROMPT_VERSION"
      head={['Task / model', 'Calls', 'Errors', 'Avg latency', 'p95', 'Tokens', 'Cost']}
      minWidth="min-w-[560px]"
    >
      {versions.map((v) => (
        <tr key={`${v.task}-${v.model}-${v.prompt_version}`}>
          <td className="px-1 py-2">
            <span className="mr-1.5 rounded-full bg-leaf-soft px-2 py-0.5 text-[10px] font-semibold text-leaf-deep">
              {v.task}
            </span>
            {v.model} <span className="text-muted">· {v.prompt_version}</span>
          </td>
          <td className="px-1 py-2 text-right">{integer(v.calls)}</td>
          <td className="px-1 py-2 text-right">{rate(v.failed_calls, v.calls)}</td>
          <td className="px-1 py-2 text-right">{duration(v.avg_latency_ms)}</td>
          <td className="px-1 py-2 text-right">{duration(v.p95_latency_ms)}</td>
          <td className="px-1 py-2 text-right">{compact(v.input_tokens + v.output_tokens)}</td>
          <td className="px-1 py-2 text-right">{v.cost_usd == null ? '—' : usd(v.cost_usd)}</td>
        </tr>
      ))}
      {versions.length === 0 && (
        <tr>
          <td colSpan={7} className="px-1 py-4 text-center text-muted">
            No model calls yet.
          </td>
        </tr>
      )}
    </Table>
  )
}

export function ToolTable({ tools }: { tools: ToolStats[] }) {
  return (
    <Table
      title="Agent tools"
      subtitle="How often the agent used each tool and how long it took"
      head={['Tool', 'Calls', 'Errors', 'Avg', 'p95']}
      minWidth="min-w-[340px]"
    >
      {tools.map((t) => (
        <tr key={t.tool}>
          <td className="px-1 py-2">{t.tool}</td>
          <td className="px-1 py-2 text-right">{integer(t.calls)}</td>
          <td className="px-1 py-2 text-right">{rate(t.failed_calls, t.calls)}</td>
          <td className="px-1 py-2 text-right">{duration(t.avg_duration_ms)}</td>
          <td className="px-1 py-2 text-right">{duration(t.p95_duration_ms)}</td>
        </tr>
      ))}
      {tools.length === 0 && (
        <tr>
          <td colSpan={5} className="px-1 py-4 text-center text-muted">
            No tool calls yet.
          </td>
        </tr>
      )}
    </Table>
  )
}

const STAGE_NAMES: Record<string, string> = {
  fetch: 'Fetch (SerpApi or cache)',
  silver: 'Read listings (silver)',
  judge: 'Judge (LLM)',
  gold: 'Build products (gold)',
}

export function StageTable({ stages }: { stages: StageStats[] }) {
  const total = stages.reduce((sum, stage) => sum + stage.avg_ms, 0)
  return (
    <Table
      title="Where search time goes"
      subtitle="Each search_offers call, split by stage. The slowest stage is the first thing to optimize."
      head={['Stage', 'Searches', 'Avg', 'p95', 'Share']}
      minWidth="min-w-[420px]"
    >
      {stages.map((s) => (
        <tr key={s.stage}>
          <td className="px-1 py-2">{STAGE_NAMES[s.stage] ?? s.stage}</td>
          <td className="px-1 py-2 text-right">{integer(s.searches)}</td>
          <td className="px-1 py-2 text-right">{duration(s.avg_ms)}</td>
          <td className="px-1 py-2 text-right">{duration(s.p95_ms)}</td>
          <td className="px-1 py-2 text-right">{percent(total > 0 ? s.avg_ms / total : null)}</td>
        </tr>
      ))}
      {stages.length === 0 && (
        <tr>
          <td colSpan={5} className="px-1 py-4 text-center text-muted">
            No timed searches yet.
          </td>
        </tr>
      )}
    </Table>
  )
}

export function RecentFailures({ failures }: { failures: FailedRun[] }) {
  return (
    <section className="glass min-w-0 p-4 sm:p-5">
      <h2 className="text-sm font-semibold">Recent failures</h2>
      <p className="mb-3 text-[11px] text-muted">The last requests that did not finish, and why</p>
      {failures.length === 0 ? (
        <p className="rounded-xl bg-leaf-soft/70 px-3 py-2.5 text-xs text-leaf-deep">No failed requests.</p>
      ) : (
        <ul className="space-y-1.5">
          {failures.map((failure) => (
            <li key={failure.request_id}>
              <Link
                to={`/requests/${failure.request_id}`}
                className="block rounded-xl bg-white/40 px-3 py-2 transition hover:bg-white/60"
              >
                <span className="flex items-center justify-between gap-2 text-[10px] text-muted">
                  <span className="truncate">{failure.description}</span>
                  <span className="shrink-0">{timeAgo(failure.created_at)}</span>
                </span>
                <span className="mt-0.5 block text-xs">{failure.error ?? 'Unknown error'}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
