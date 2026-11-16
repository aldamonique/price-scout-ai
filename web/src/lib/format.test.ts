import { describe, expect, it } from 'vitest'

import { budgetLabel, compact, countryName, currencySymbol, duration, installments, integer, money, percent, seconds, timeAgo, usd } from './format'

describe('format', () => {
  it('writes prices in the market currency', () => {
    expect(money(1299.5, 'BRL')).toBe('R$1,299.50')
    expect(money(1299.5, 'EUR')).toBe('€1,299.50')
  })

  it('finds the symbol shown before the budget', () => {
    expect(currencySymbol('BRL')).toBe('R$')
    expect(currencySymbol('USD')).toBe('$')
  })

  it('writes installments only when there are two or more', () => {
    expect(installments(10, 129.9, 'BRL')).toBe('10× R$129.90')
    expect(installments(12, null, 'BRL')).toBe('up to 12×')
    expect(installments(1, 100, 'BRL')).toBeNull()
    expect(installments(null, null, 'BRL')).toBeNull()
  })

  it('writes the country name from its code', () => {
    expect(countryName('br')).toBe('Brazil')
  })

  it('writes durations in seconds with one decimal', () => {
    expect(seconds(9840)).toBe('9.8 s')
  })

  it('writes whole numbers with thousand separators', () => {
    expect(integer(18400)).toBe('18,400')
  })

  it('says the cost is unavailable instead of showing zero', () => {
    expect(usd(null)).toBe('cost unavailable')
    expect(usd(0.0912)).toBe('$0.091')
  })

  it('writes how long ago a request was made', () => {
    const now = new Date('2026-11-15T12:00:00Z')
    expect(timeAgo('2026-11-15T11:59:50Z', now)).toBe('just now')
    expect(timeAgo('2026-11-15T11:55:00Z', now)).toBe('5 minutes ago')
    expect(timeAgo('2026-11-14T12:00:00Z', now)).toBe('yesterday')
    expect(timeAgo('2026-11-01T12:00:00Z', now)).toBe('Nov 1')
  })

  it('names the budget, or says there is none', () => {
    expect(budgetLabel(3000, 'BRL')).toBe('Budget R$3,000.00')
    expect(budgetLabel(null, 'BRL')).toBe('No budget')
  })

  it('writes rates as percentages and a dash when there is none', () => {
    expect(percent(0.5)).toBe('50%')
    expect(percent(1 / 3)).toBe('33.3%')
    expect(percent(null)).toBe('—')
  })

  it('writes latencies in ms below a second and in seconds above', () => {
    expect(duration(850)).toBe('850 ms')
    expect(duration(1240)).toBe('1.2 s')
    expect(duration(null)).toBe('—')
  })

  it('writes large counts in compact form', () => {
    expect(compact(18400)).toBe('18.4K')
    expect(compact(2_300_000)).toBe('2.3M')
  })
})
