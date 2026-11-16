import { describe, expect, it } from 'vitest'

import type { RequestSummary } from '../../api/types'
import { countByStatus, filterRequests } from './filter'

function summary(id: string, description: string, status: RequestSummary['status'], country = 'br'): RequestSummary {
  return {
    id,
    description,
    market: { country, language: 'en', currency: 'BRL' },
    budget: 3000,
    status,
    total: null,
    item_count: 0,
    created_at: '2026-11-15T12:00:00Z',
  }
}

const REQUESTS = [
  summary('a', 'Living room sofa and TV stand', 'done'),
  summary('b', 'Home office desk', 'running'),
  summary('c', 'Bedroom wardrobe', 'queued', 'pt'),
  summary('d', 'Dining table', 'failed'),
]

describe('filterRequests', () => {
  it('finds every word in the description, in any case', () => {
    expect(filterRequests(REQUESTS, 'sofa LIVING', 'all').map((r) => r.id)).toEqual(['a'])
  })

  it('also searches the country name', () => {
    expect(filterRequests(REQUESTS, 'portugal', 'all').map((r) => r.id)).toEqual(['c'])
  })

  it('counts queued requests as running', () => {
    expect(filterRequests(REQUESTS, '', 'running').map((r) => r.id)).toEqual(['b', 'c'])
    expect(countByStatus(REQUESTS, 'running')).toBe(2)
    expect(countByStatus(REQUESTS, 'all')).toBe(4)
  })
})
