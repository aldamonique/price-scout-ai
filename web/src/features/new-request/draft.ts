import type { Preferences, ShoppingRequestBody } from '../../api/types'

export interface RequestDraft {
  description: string
  country: string
  budget: string
  brands: string
  colors: string
  materials: string
  payment: string
  notes: string
}

export type PreferenceField = keyof Required<Preferences>

export const MIN_DESCRIPTION = 10

export const EMPTY_DRAFT: RequestDraft = {
  description: '',
  country: 'br',
  budget: '',
  brands: '',
  colors: '',
  materials: '',
  payment: '',
  notes: '',
}

export const EXAMPLES: { label: string; description: string; budget: string }[] = [
  {
    label: 'Living room',
    description:
      'Furnish a 3 x 4 m living room: a sofa, a TV stand and a coffee table. The TV wall is 2.10 m wide.',
    budget: '6000',
  },
  {
    label: 'Home office',
    description: 'For my home office: a mechanical keyboard ABNT2, a wireless Logitech mouse and a 27-inch monitor.',
    budget: '2500',
  },
  {
    label: 'Supplements',
    description: 'Whey protein isolate 900 g, vanilla flavor, and creatine monohydrate 300 g.',
    budget: '',
  },
]

export const EXAMPLE_DRAFT: RequestDraft = {
  description:
    'Furnish a 3 x 4 m living room: a sofa, a TV stand and a coffee table. ' +
    'The TV wall is 2.10 m wide.',
  country: 'br',
  budget: '6000',
  brands: '',
  colors: 'gray, beige',
  materials: '',
  payment: 'up to 10 interest-free installments',
  notes: '',
}

export function parseBudget(text: string): number | null {
  const value = Number(text.replace(',', '.'))
  return text.trim() !== '' && Number.isFinite(value) && value > 0 ? value : null
}

export function hasValidBudget(draft: RequestDraft): boolean {
  return draft.budget.trim() === '' || parseBudget(draft.budget) !== null
}

export function isReady(draft: RequestDraft): boolean {
  return draft.description.trim().length >= MIN_DESCRIPTION && draft.country !== '' && hasValidBudget(draft)
}

function optional(text: string): string | null {
  const trimmed = text.trim()
  return trimmed === '' ? null : trimmed
}

export function toRequestBody(draft: RequestDraft): ShoppingRequestBody {
  return {
    description: draft.description.trim(),
    country: draft.country,
    budget: parseBudget(draft.budget),
    preferences: {
      brands: optional(draft.brands),
      colors: optional(draft.colors),
      materials: optional(draft.materials),
      payment: optional(draft.payment),
      notes: optional(draft.notes),
    },
  }
}

export function preferenceCount(draft: RequestDraft): number {
  return [draft.brands, draft.colors, draft.materials, draft.payment, draft.notes].filter((v) => v.trim() !== '').length
}
