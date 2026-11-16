import { LoaderCircle, TriangleAlert } from 'lucide-react'

import type { ShoppingRequest } from '../../api/types'
import { GlassCard } from '../../components/GlassCard'
import { StepTimeline } from './StepTimeline'

export function RequestProgress({ request }: { request: ShoppingRequest }) {
  return (
    <GlassCard
      title="The agent is working"
      subtitle="A request takes from 30 seconds to 2 minutes. You can leave and come back."
      icon={LoaderCircle}
      iconClassName="animate-spin"
    >
      <StepTimeline steps={request.steps} working />
    </GlassCard>
  )
}

export function RequestFailed({ request }: { request: ShoppingRequest }) {
  return (
    <GlassCard
      title="The request did not finish"
      subtitle={request.error ?? undefined}
      icon={TriangleAlert}
    >
      {request.error && <p className="mb-3 rounded-xl bg-blush-soft px-3 py-2 text-xs text-blush">{request.error}</p>}
      {request.steps.length > 0 && <StepTimeline steps={request.steps} />}
    </GlassCard>
  )
}

export function RequestNotice({ message }: { message: string }) {
  return (
    <GlassCard>
      <p role="status" className="text-xs text-muted">
        {message}
      </p>
    </GlassCard>
  )
}
