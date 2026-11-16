import { RefreshCw } from 'lucide-react'

import { PageHeader } from '../../components/PageHeader'
import { AdminTokenForm } from './AdminTokenForm'
import { DailyUsageChart } from './DailyUsageChart'
import { JudgeAccuracy } from './JudgeAccuracy'
import { OverviewTiles } from './OverviewTiles'
import { RecentFailures, StageTable, ToolTable, VersionTable } from './UsageTables'
import { useObservability } from './useObservability'

export function ObservabilityPage() {
  const { overview, runs, error, locked, loading, refresh } = useObservability()

  return (
    <div className="mx-auto max-w-none space-y-5">
      <PageHeader
        title="Observability"
        subtitle="Every agent run and model call: cost, latency, errors, tools and prompt versions."
        actions={
          <button
            type="button"
            onClick={refresh}
            disabled={loading}
            className="glass inline-flex items-center gap-1.5 rounded-full! px-4 py-2 text-xs font-medium transition hover:bg-white/60 disabled:opacity-60"
          >
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        }
      />

      {error && (
        <p role="alert" className="glass rounded-2xl! px-4 py-3 text-xs text-muted">
          {error}
        </p>
      )}
      {locked && <AdminTokenForm onSaved={refresh} />}
      {!overview && !error && <p className="text-xs text-muted">Loading...</p>}

      {overview && (
        <>
          <OverviewTiles overview={overview} />
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
            <DailyUsageChart daily={overview.daily} />
            <RecentFailures failures={overview.recent_failures} />
          </div>
          <JudgeAccuracy runs={runs} />
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
            <VersionTable versions={overview.by_version} />
            <ToolTable tools={overview.tools} />
          </div>
          <StageTable stages={overview.stages} />
        </>
      )}
    </div>
  )
}
