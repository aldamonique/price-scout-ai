import { Plus } from 'lucide-react'
import { Link } from 'react-router'

export function NewRequestButton() {
  return (
    <Link
      to="/"
      className="primary-action inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition"
    >
      <Plus className="size-3.5" /> New request
    </Link>
  )
}
