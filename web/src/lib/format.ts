const decimal = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 })
const whole = new Intl.NumberFormat('en-US')
const dollars = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 3,
})
const countries = new Intl.DisplayNames(['en'], { type: 'region' })
const relative = new Intl.RelativeTimeFormat('en', { numeric: 'auto' })
const dateOnly = new Intl.DateTimeFormat('en-US', { day: 'numeric', month: 'short' })

export function money(value: number, currency: string): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(value)
}

export function budgetLabel(budget: number | null | undefined, currency: string): string {
  return budget == null ? 'No budget' : `Budget ${money(budget, currency)}`
}

export function currencySymbol(currency: string): string {
  const parts = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    currencyDisplay: 'narrowSymbol',
  }).formatToParts(0)
  return parts.find((part) => part.type === 'currency')?.value ?? currency
}

export function installments(months: number | null | undefined, amount: number | null | undefined, currency: string): string | null {
  if (!months || months < 2) return null
  return amount ? `${months}× ${money(amount, currency)}` : `up to ${months}×`
}

export function countryName(code: string): string {
  return countries.of(code.toUpperCase()) ?? code.toUpperCase()
}

export function seconds(milliseconds: number): string {
  return `${decimal.format(milliseconds / 1000)} s`
}

export function integer(value: number): string {
  return whole.format(value)
}

export function usd(value: number | null | undefined): string {
  return value == null ? 'cost unavailable' : dollars.format(value)
}

export function timeAgo(iso: string, now: Date = new Date()): string {
  const minutes = Math.round((now.getTime() - Date.parse(iso)) / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return relative.format(-minutes, 'minute')
  const hours = Math.round(minutes / 60)
  if (hours < 24) return relative.format(-hours, 'hour')
  const days = Math.round(hours / 24)
  return days < 7 ? relative.format(-days, 'day') : dateOnly.format(new Date(iso))
}

const percentFormat = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 1 })

export function percent(rate: number | null | undefined): string {
  return rate == null ? '—' : percentFormat.format(rate)
}

export function duration(milliseconds: number | null | undefined): string {
  if (milliseconds == null) return '—'
  return milliseconds < 1000 ? `${Math.round(milliseconds)} ms` : seconds(milliseconds)
}

export function compact(value: number): string {
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
}
