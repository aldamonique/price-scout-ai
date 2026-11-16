import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

interface GlassCardProps {
  title?: string
  subtitle?: string
  icon?: LucideIcon
  iconClassName?: string
  action?: ReactNode
  className?: string
  children: ReactNode
}

export function GlassCard({
  title,
  subtitle,
  icon: Icon,
  iconClassName = '',
  action,
  className = '',
  children,
}: GlassCardProps) {
  return (
    <section className={`glass p-4 sm:p-5 ${className}`}>
      {title && (
        <header className="mb-3 flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2.5">
            {Icon && (
              <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-white/50">
                <Icon className={`size-4 text-blush ${iconClassName}`} strokeWidth={1.9} />
              </span>
            )}
            <div className="min-w-0">
              <h2 className="text-sm font-semibold">{title}</h2>
              {subtitle && <p className="truncate text-xs text-muted">{subtitle}</p>}
            </div>
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  )
}
