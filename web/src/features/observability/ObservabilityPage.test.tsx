import { act, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError } from '../../api/client'
import { evalRun, OVERVIEW } from '../../test/fixtures'
import { ObservabilityPage } from './ObservabilityPage'

async function renderPage() {
  render(
    <MemoryRouter>
      <ObservabilityPage />
    </MemoryRouter>,
  )
  await act(async () => {})
}

describe('ObservabilityPage', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    window.localStorage.clear()
  })

  beforeEach(() => {
    vi.spyOn(api, 'listEvalRuns').mockResolvedValue([evalRun()])
  })

  it('shows the headline numbers, the tables and the failures', async () => {
    vi.spyOn(api, 'getObservability').mockResolvedValue(OVERVIEW)

    await renderPage()

    expect(screen.getByText('$0.27')).toBeTruthy()
    expect(screen.getByText('75%')).toBeTruthy()
    expect(screen.getByText('search_offers')).toBeTruthy()
    expect(screen.getByText('SerpApi failed (401)')).toBeTruthy()
    expect(screen.getByRole('link', { name: /A queen bed/ }).getAttribute('href')).toBe('/requests/r4')
  })

  it('reloads the data on refresh', async () => {
    const getObservability = vi.spyOn(api, 'getObservability').mockResolvedValue(OVERVIEW)
    await renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }))
    await act(async () => {})

    expect(getObservability).toHaveBeenCalledTimes(2)
  })

  it('tells how to fix missing dbt views', async () => {
    vi.spyOn(api, 'getObservability').mockRejectedValue(
      new ApiError(503, 'The observability views are missing. Run dbt build in analytics/.'),
    )

    await renderPage()

    expect(screen.getByRole('alert').textContent).toContain('dbt build')
  })

  it('shows where search time goes and the judge accuracy', async () => {
    vi.spyOn(api, 'getObservability').mockResolvedValue(OVERVIEW)

    await renderPage()

    expect(screen.getByText('Judge (LLM)')).toBeTruthy()
    expect(screen.getByText('77.8%')).toBeTruthy()
    expect(screen.getByText('Judge accuracy')).toBeTruthy()
  })

  it('asks for the admin token when the API is protected, then retries', async () => {
    const getObservability = vi
      .spyOn(api, 'getObservability')
      .mockRejectedValueOnce(new ApiError(401, 'This action needs the admin token.'))
      .mockResolvedValueOnce(OVERVIEW)
    await renderPage()

    fireEvent.change(screen.getByLabelText(/Admin token/), { target: { value: 'secret' } })
    fireEvent.click(screen.getByRole('button', { name: 'Unlock' }))
    await act(async () => {})

    expect(window.localStorage.getItem('price-scout.admin-token')).toBe('secret')
    expect(getObservability).toHaveBeenCalledTimes(2)
    expect(screen.getByText('$0.27')).toBeTruthy()
  })
})
