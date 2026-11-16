import { describe, expect, it } from 'vitest'

import { EMPTY_DRAFT, EXAMPLE_DRAFT, isReady, parseBudget, preferenceCount, toRequestBody } from './draft'

describe('request draft', () => {
  it('reads the budget with a dot or a comma', () => {
    expect(parseBudget('6000')).toBe(6000)
    expect(parseBudget('2499,90')).toBe(2499.9)
    expect(parseBudget('')).toBeNull()
    expect(parseBudget('-5')).toBeNull()
  })

  it('is ready with a description and a country; the budget is optional', () => {
    expect(isReady(EXAMPLE_DRAFT)).toBe(true)
    expect(isReady({ ...EXAMPLE_DRAFT, budget: '' })).toBe(true)
    expect(isReady({ ...EXAMPLE_DRAFT, description: 'sofa' })).toBe(false)
    expect(isReady({ ...EXAMPLE_DRAFT, budget: '-5' })).toBe(false)
  })

  it('sends no budget when the field is empty', () => {
    expect(toRequestBody({ ...EXAMPLE_DRAFT, budget: '' }).budget).toBeNull()
  })

  it('sends empty preferences as null and trims the rest', () => {
    const body = toRequestBody({ ...EXAMPLE_DRAFT, brands: '  Tok&Stok ', materials: '  ' })

    expect(body.budget).toBe(6000)
    expect(body.preferences).toEqual({
      brands: 'Tok&Stok',
      colors: 'gray, beige',
      materials: null,
      payment: 'up to 10 interest-free installments',
      notes: null,
    })
  })

  it('counts the preferences filled in', () => {
    expect(preferenceCount(EMPTY_DRAFT)).toBe(0)
    expect(preferenceCount(EXAMPLE_DRAFT)).toBe(2)
  })
})
