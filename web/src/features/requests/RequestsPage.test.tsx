import { act, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { api } from '../../api/client'
import { summary } from '../../test/fixtures'
import { RequestsPage } from './RequestsPage'

const REQUESTS = [
  summary({ id: 'a', description: 'Living room sofa', status: 'done' }),
  summary({ id: 'b', description: 'Home office desk', status: 'failed', total: null, item_count: 0 }),
  summary({ id: 'c', description: 'Bedroom wardrobe', status: 'done' }),
]

async function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <RequestsPage />
    </MemoryRouter>,
  )
  await act(async () => {})
}

function descriptions(): string[] {
  return screen.queryAllByRole('link').map((link) => link.textContent ?? '')
}

describe('RequestsPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('lists every request with a link to its page', async () => {
    vi.spyOn(api, 'listRequests').mockResolvedValue(REQUESTS)

    await renderAt('/requests')

    const rows = screen.getAllByRole('link').filter((link) => link.getAttribute('href')?.startsWith('/requests/'))
    expect(rows.map((row) => row.getAttribute('href'))).toEqual(['/requests/a', '/requests/b', '/requests/c'])
  })

  it('applies the search from the address bar', async () => {
    vi.spyOn(api, 'listRequests').mockResolvedValue(REQUESTS)

    await renderAt('/requests?q=desk')

    expect(descriptions().some((text) => text.includes('Home office desk'))).toBe(true)
    expect(descriptions().some((text) => text.includes('Living room sofa'))).toBe(false)
  })

  it('filters by status and shows the count of each', async () => {
    vi.spyOn(api, 'listRequests').mockResolvedValue(REQUESTS)
    await renderAt('/requests')

    fireEvent.click(screen.getByRole('tab', { name: /Failed/ }))

    expect(screen.getByRole('tab', { name: /Done/ }).textContent).toContain('2')
    expect(descriptions().filter((text) => text.includes('desk'))).toHaveLength(1)
    expect(descriptions().some((text) => text.includes('sofa'))).toBe(false)
  })

  it('explains when nothing matches', async () => {
    vi.spyOn(api, 'listRequests').mockResolvedValue(REQUESTS)

    await renderAt('/requests?q=piano')

    expect(screen.getByText('No request matches the search.')).toBeTruthy()
  })

  it('says when the API cannot be reached', async () => {
    vi.spyOn(api, 'listRequests').mockRejectedValue(new TypeError('Failed to fetch'))

    await renderAt('/requests')

    expect(screen.getByText('Could not load the requests. Is the API running?')).toBeTruthy()
  })
})
