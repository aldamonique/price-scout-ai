import { ArrowRight, CircleCheck, Package, PiggyBank, Replace, Ruler, Store } from 'lucide-react'

import type { PlanItem } from '../../api/types'
import { StoreBadge } from '../../components/StoreBadge'
import { money } from '../../lib/format'

interface PlanItemCardProps {
  item: PlanItem
  currency: string
  selected: boolean
  onSelect: () => void
}

function SizeLine({ item }: { item: PlanItem }) {
  const { product, fits } = item
  if (product.category !== 'furniture' && fits == null) return null
  return (
    <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted">
      <span>{product.dimensions ?? 'size not listed'}</span>
      {fits === true && (
        <span className="inline-flex items-center gap-1 rounded-full bg-mint-soft px-2 py-0.5 text-mint">
          <CircleCheck className="size-3" /> fits the space
        </span>
      )}
      {fits === false && (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-soft px-2 py-0.5 text-amber">
          <Ruler className="size-3" /> does not fit
        </span>
      )}
    </div>
  )
}

export function PlanItemCard({ item, currency, selected, onSelect }: PlanItemCardProps) {
  const { product } = item
  const cheapest = product.offers[0]
  const stores = product.store_count

  return (
    <article
      className={`flex flex-col overflow-hidden rounded-2xl border bg-white/75 shadow-[0_1px_2px_rgba(30,28,38,0.06)] transition hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(30,28,38,0.08)] ${
        selected ? 'border-leaf ring-2 ring-leaf/25' : 'border-white/80'
      }`}
    >
      <button type="button" onClick={onSelect} className="relative block h-44 bg-white" tabIndex={-1}>
        {product.image_url ? (
          <img src={product.image_url} alt="" className="size-full object-contain p-2" />
        ) : (
          <span className="grid size-full place-items-center">
            <Package className="size-8 text-muted" />
          </span>
        )}
        <span className="absolute top-2.5 left-2.5 rounded-full bg-ink/85 px-2.5 py-1 text-[10px] font-semibold tracking-wide text-white uppercase">
          {item.item}
        </span>
        {item.differences && (
          <span className="absolute top-2.5 right-2.5 inline-flex items-center gap-1 rounded-full bg-amber-soft px-2 py-1 text-[10px] font-semibold text-amber">
            <Replace className="size-3" /> Similar match
          </span>
        )}
        <span
          className={`absolute bottom-2.5 left-2.5 inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ${
            stores > 1 ? 'bg-leaf text-white' : 'bg-white/90 text-muted ring-1 ring-black/5'
          }`}
        >
          <Store className="size-3" />
          {stores > 1 ? `${stores} stores` : 'Single store'}
        </span>
      </button>

      <div className="flex flex-1 flex-col gap-1.5 p-3">
        <h3 className="line-clamp-2 text-sm leading-snug font-semibold">{product.name}</h3>
        <SizeLine item={item} />

        <div className="flex items-end justify-between gap-2">
          <div>
            <p className="text-[10px] text-muted">{stores > 1 ? 'Lowest price' : 'Price'}</p>
            <p className="text-lg leading-none font-bold tracking-tight">{money(product.min_price, currency)}</p>
          </div>
          {cheapest && (
            <span className="flex min-w-0 items-center gap-1.5 text-[11px] text-muted">
              <StoreBadge store={cheapest.store} icon={cheapest.store_icon} size="sm" />
              <span className="truncate">{cheapest.store}</span>
            </span>
          )}
        </div>

        {item.savings > 0 && (
          <p className="inline-flex w-fit items-center gap-1 rounded-full bg-leaf-soft px-2 py-0.5 text-[11px] font-medium text-leaf-deep">
            <PiggyBank className="size-3.5" /> Save up to {money(item.savings, currency)}
          </p>
        )}

        <p className="line-clamp-2 text-[11px] leading-relaxed text-muted" title={item.reason}>{item.reason}</p>
        {item.differences && (
          <p className="rounded-lg bg-amber-soft/60 px-2 py-1 text-[11px]">
            <span className="font-semibold">Differs from your request: </span>
            {item.differences}
          </p>
        )}

        <button
          type="button"
          onClick={onSelect}
          aria-pressed={selected}
          className={`mt-auto inline-flex items-center justify-center gap-1 rounded-lg px-3 py-1.5 text-[11px] font-semibold transition ${
            selected ? 'bg-leaf text-white' : 'bg-ink/5 text-ink hover:bg-ink/10'
          }`}
        >
          {selected ? 'Comparing stores' : 'Compare stores'} <ArrowRight className="size-3.5" />
        </button>
      </div>
    </article>
  )
}
