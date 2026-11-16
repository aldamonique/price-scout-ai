import { ChevronDown, LoaderCircle, SlidersHorizontal } from 'lucide-react'
import { useState, type FormEvent, type ReactNode } from 'react'

import type { Market } from '../../api/types'
import { countryName, currencySymbol } from '../../lib/format'
import {
  EXAMPLES,
  hasValidBudget,
  isReady,
  MIN_DESCRIPTION,
  preferenceCount,
  type PreferenceField,
  type RequestDraft,
} from './draft'

interface RequestComposerProps {
  draft: RequestDraft
  markets: Market[]
  submitting: boolean
  error: string | null
  onChange: (draft: RequestDraft) => void
  onSubmit: () => void
}

const PREFERENCES: { field: PreferenceField; label: string; placeholder: string; wide?: boolean }[] = [
  { field: 'brands', label: 'Preferred brands', placeholder: 'e.g. Tok&Stok, Etna' },
  { field: 'colors', label: 'Colors', placeholder: 'e.g. gray, beige' },
  { field: 'materials', label: 'Materials', placeholder: 'e.g. solid wood, linen' },
  { field: 'payment', label: 'Payment terms', placeholder: 'e.g. up to 10 installments' },
  { field: 'notes', label: 'Other requirements', placeholder: 'e.g. pet-friendly fabric', wide: true },
]

function Field({ id, label, children }: { id: string; label: string; children: ReactNode }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-[11px] font-medium text-muted">
        {label}
      </label>
      {children}
    </div>
  )
}

export function RequestComposer({ draft, markets, submitting, error, onChange, onSubmit }: RequestComposerProps) {
  const [showPreferences, setShowPreferences] = useState(false)
  const market = markets.find((m) => m.country === draft.country)
  const canSubmit = isReady(draft) && market !== undefined && !submitting
  const filled = preferenceCount(draft)

  function set<K extends keyof RequestDraft>(key: K, value: RequestDraft[K]) {
    onChange({ ...draft, [key]: value })
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (canSubmit) onSubmit()
  }

  const missing =
    draft.description.trim().length < MIN_DESCRIPTION
      ? 'Describe what you need to start.'
      : !hasValidBudget(draft)
        ? 'The budget must be a number above zero, or empty.'
        : 'Takes 30 seconds to 2 minutes. You can leave and come back.'

  return (
    <form onSubmit={handleSubmit} className="glass request-composer space-y-5 p-5 sm:p-6">
      <div className="border-b border-white/65 pb-4">
        <p className="text-base font-semibold tracking-tight">Start with your space</p>
        <p className="mt-0.5 text-xs leading-relaxed text-muted sm:text-sm">A few details help the agent find a plan that fits.</p>
      </div>
      <div>
        <label htmlFor="description" className="mb-1.5 block text-xs font-semibold">
          What do you want to buy?
        </label>
        <textarea
          id="description"
          value={draft.description}
          onChange={(event) => set('description', event.target.value)}
          rows={4}
          maxLength={600}
          placeholder="E.g.: a wireless mouse, Mrs Dalloway in paperback and whey protein 900 g. Or a sofa for a 2.10 m wall."
          className="field resize-none p-3.5! text-sm! leading-relaxed placeholder:text-muted/80"
        />
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-muted">Try:</span>
          {EXAMPLES.map((example) => (
            <button
              key={example.label}
              type="button"
              onClick={() => onChange({ ...draft, description: example.description, budget: example.budget })}
              className="rounded-full border border-white/80 bg-white/45 px-3 py-1.5 text-[11px] font-medium shadow-[0_4px_12px_rgb(48_43_50/.06),inset_0_1px_0_rgb(255_255_255/.85)] backdrop-blur-md transition hover:-translate-y-0.5 hover:bg-white/70"
            >
              {example.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Field id="country" label="Country">
          <select
            id="country"
            value={draft.country}
            onChange={(event) => set('country', event.target.value)}
            className="field"
          >
            {markets.length === 0 && <option value={draft.country}>Loading...</option>}
            {markets.map((m) => (
              <option key={m.country} value={m.country}>
                {countryName(m.country)} · {m.currency}
              </option>
            ))}
          </select>
        </Field>
        <Field id="budget" label={market ? `Budget (${market.currency}, optional)` : 'Budget (optional)'}>
          <div className="field flex items-center gap-1.5">
            <span className="text-xs text-muted">{market ? currencySymbol(market.currency) : ''}</span>
            <input
              id="budget"
              inputMode="decimal"
              value={draft.budget}
              onChange={(event) => set('budget', event.target.value)}
              placeholder="No limit"
              className="w-full min-w-0 bg-transparent outline-none"
            />
          </div>
        </Field>
      </div>

      <div className="border-t border-white/60 pt-1">
        <button
          type="button"
          onClick={() => setShowPreferences((open) => !open)}
          aria-expanded={showPreferences}
          aria-controls="preferences"
          className="flex w-full items-center gap-2 py-2.5 text-left text-xs"
        >
          <SlidersHorizontal className="size-3.5 text-blush" />
          <span className="font-medium">Preferences</span>
          <span className="min-w-0 truncate text-muted">
            {filled > 0 ? `${filled} set` : 'optional: brands, colors, materials, payment'}
          </span>
          <ChevronDown className={`ml-auto size-4 shrink-0 text-muted transition ${showPreferences ? 'rotate-180' : ''}`} />
        </button>
        {showPreferences && (
          <div id="preferences" className="grid gap-3 rounded-2xl bg-white/20 p-3 pb-4 sm:grid-cols-2">
            {PREFERENCES.map(({ field, label, placeholder, wide }) => (
              <div key={field} className={wide ? 'sm:col-span-2' : undefined}>
                <Field id={field} label={label}>
                  <input
                    id={field}
                    value={draft[field]}
                    onChange={(event) => set(field, event.target.value)}
                    maxLength={field === 'notes' ? 400 : 200}
                    placeholder={placeholder}
                    className="field placeholder:text-muted/70"
                  />
                </Field>
              </div>
            ))}
          </div>
        )}
      </div>

      {error && (
        <p role="alert" className="rounded-xl border border-white/75 bg-white/48 px-3 py-2 text-xs text-muted shadow-[inset_0_1px_0_rgb(255_255_255/.85)]">
          {error}
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/60 pt-4">
        <p className="text-[11px] text-muted">{missing}</p>
        <button
          type="submit"
          disabled={!canSubmit}
          className="primary-action flex items-center gap-2 rounded-full px-6 py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-85"
        >
          {submitting && <LoaderCircle className="size-4 animate-spin" />}
          {submitting ? 'Sending...' : 'Run request'}
        </button>
      </div>
    </form>
  )
}
