import type { Overview } from '../../api/types'
import { overviewTiles } from './tiles'

export function OverviewTiles({ overview }: { overview: Overview }) {
  return (
    <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 2xl:grid-cols-6">
      {overviewTiles(overview).map(({ label, value, hint, icon: Icon, highlight }) => (
        <li
          key={label}
          className={`${highlight ? 'leaf-card' : 'glass'} flex min-w-0 flex-col gap-2 rounded-2xl! p-3.5`}
        >
          <span className="flex items-center gap-1.5">
            <Icon className={`size-3.5 ${highlight ? 'text-white/80' : 'text-muted'}`} />
            <span className={`truncate text-[11px] ${highlight ? 'text-white/80' : 'text-muted'}`}>{label}</span>
          </span>
          <span className="text-xl font-semibold tracking-tight">{value}</span>
          <span className={`truncate text-[10px] ${highlight ? 'text-white/70' : 'text-muted'}`}>{hint}</span>
        </li>
      ))}
    </ul>
  )
}
