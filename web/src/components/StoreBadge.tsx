import { useState } from 'react'

import { colorFor } from '../lib/storeColor'

interface StoreBadgeProps {
  store: string
  icon?: string | null
  size?: 'sm' | 'md'
}

export function StoreBadge({ store, icon, size = 'md' }: StoreBadgeProps) {
  const [failed, setFailed] = useState(false)
  const box = size === 'sm' ? 'size-7 text-xs' : 'size-9 text-sm'

  if (icon && !failed) {
    return (
      <img
        src={icon}
        alt={store}
        onError={() => setFailed(true)}
        className={`${box} shrink-0 rounded-xl bg-white object-contain p-1`}
      />
    )
  }

  return (
    <span
      role="img"
      aria-label={store}
      className={`${box} grid shrink-0 place-items-center rounded-full font-bold text-white`}
      style={{ backgroundColor: colorFor(store) }}
    >
      {store.trim().charAt(0).toUpperCase()}
    </span>
  )
}
