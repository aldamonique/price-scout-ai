import { Search } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'

export function WorkspaceSearch() {
  const navigate = useNavigate()
  const [text, setText] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const query = text.trim()
    navigate(query ? `/requests?q=${encodeURIComponent(query)}` : '/requests')
  }

  return (
    <form role="search" onSubmit={handleSubmit} className="relative w-full sm:w-64">
      <Search className="pointer-events-none absolute top-1/2 left-3.5 size-3.5 -translate-y-1/2 text-muted" />
      <input
        type="search"
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="Search requests..."
        aria-label="Search requests"
        className="h-10 w-full rounded-full border border-white/80 bg-white/65 py-2 pr-4 pl-9 text-xs shadow-[0_6px_18px_rgb(54_48_58/.06),inset_0_1px_0_rgb(255_255_255/.9)] outline-none backdrop-blur-xl transition focus:bg-white/85 focus:ring-2 focus:ring-lilac/30 placeholder:text-muted"
      />
    </form>
  )
}
