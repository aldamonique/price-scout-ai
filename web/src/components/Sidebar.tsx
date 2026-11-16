import { Activity, History, PencilLine } from 'lucide-react'
import { Link, useLocation } from 'react-router'

const LINKS = [
  { to: '/', label: 'New request', icon: PencilLine },
  { to: '/requests', label: 'Requests', icon: History },
  { to: '/observability', label: 'Observability', icon: Activity },
]

function isActive(to: string, pathname: string): boolean {
  return to === '/' ? pathname === '/' : pathname === to || pathname.startsWith(`${to}/`)
}

export function Sidebar() {
  const { pathname } = useLocation()

  return (
    <aside className="dashboard-sidebar flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-white/75 px-4 py-3 sm:px-6 sm:py-4 lg:flex-nowrap lg:flex-col lg:items-stretch lg:gap-0 lg:border-r lg:border-b-0 lg:px-6 lg:py-8">
      <Link to="/" className="flex shrink-0 items-center gap-3 lg:px-1">
        <img
          src="/3d-sphere.png"
          alt=""
          aria-hidden="true"
          className="size-10 object-contain drop-shadow-[0_5px_10px_rgb(158_120_162/.2)] sm:size-11 lg:size-14"
        />
        <span className="text-lg font-semibold tracking-tight lg:text-2xl">Price Scout</span>
      </Link>

      <p className="mt-12 hidden px-3 text-[11px] font-semibold tracking-[0.2em] text-muted lg:block">WORKSPACE</p>
      <nav
        aria-label="Main"
        className="order-3 flex w-full gap-1 overflow-x-auto py-1 lg:order-none lg:mt-3 lg:flex-col lg:gap-1.5 lg:overflow-visible"
      >
        {LINKS.map(({ to, label, icon: Icon }) => {
          const active = isActive(to, pathname)
          return (
            <Link
              key={to}
              to={to}
              aria-current={active ? 'page' : undefined}
              className={`flex items-center gap-3 whitespace-nowrap rounded-xl px-3 py-2.5 text-sm transition lg:rounded-2xl lg:px-4 lg:py-3.5 lg:text-[15px] ${
                active
                  ? 'bg-[#29282d] font-semibold text-white shadow-[0_8px_18px_rgb(41_40_45/.2)]'
                  : 'text-ink/80 hover:bg-white/60 hover:text-ink'
              }`}
            >
              <Icon className="size-4 lg:size-5" />
              {label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
