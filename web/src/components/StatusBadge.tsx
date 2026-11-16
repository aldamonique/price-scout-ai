import { CircleCheck, CircleX, Clock, LoaderCircle, type LucideIcon } from 'lucide-react'

import type { RequestStatus } from '../api/types'

const STATUS: Record<RequestStatus, { label: string; icon: LucideIcon; className: string }> = {
  queued: { label: 'Queued', icon: Clock, className: 'bg-white/50 text-muted' },
  running: { label: 'Running', icon: LoaderCircle, className: 'bg-lilac-soft/80 text-lilac' },
  done: { label: 'Done', icon: CircleCheck, className: 'bg-mint-soft/80 text-mint' },
  failed: { label: 'Failed', icon: CircleX, className: 'bg-blush-soft/80 text-blush' },
}

export function StatusBadge({ status }: { status: RequestStatus }) {
  const { label, icon: Icon, className } = STATUS[status]
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${className}`}>
      <Icon className={`size-3 ${status === 'running' ? 'animate-spin' : ''}`} />
      {label}
    </span>
  )
}
