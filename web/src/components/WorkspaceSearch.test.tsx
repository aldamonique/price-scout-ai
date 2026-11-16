import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router'
import { describe, expect, it } from 'vitest'

import { WorkspaceSearch } from './WorkspaceSearch'

function Location() {
  const { pathname, search } = useLocation()
  return <p data-testid="location">{pathname + search}</p>
}

function renderSearch() {
  render(
    <MemoryRouter initialEntries={['/']}>
      <WorkspaceSearch />
      <Routes>
        <Route path="*" element={<Location />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('WorkspaceSearch', () => {
  it('opens the request list filtered by the text', () => {
    renderSearch()

    fireEvent.change(screen.getByRole('searchbox', { name: 'Search requests' }), { target: { value: ' sofa ' } })
    fireEvent.submit(screen.getByRole('search'))

    expect(screen.getByTestId('location').textContent).toBe('/requests?q=sofa')
  })

  it('opens the whole list when the text is empty', () => {
    renderSearch()

    fireEvent.submit(screen.getByRole('search'))

    expect(screen.getByTestId('location').textContent).toBe('/requests')
  })
})
