import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  subtitle?: ReactNode
  eyebrow?: ReactNode
  actions?: ReactNode
}

export function PageHeader({ title, subtitle, eyebrow, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        {eyebrow && <div className="mb-1 text-xs text-muted">{eyebrow}</div>}
        <h1 className="text-3xl font-semibold tracking-[-0.04em] sm:text-1xl">{title}</h1>
        {subtitle && <div className="mt-1.5 max-w-2xl text-sm leading-relaxed text-muted sm:text-base">{subtitle}</div>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  )
}
