import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, it } from 'vitest'

import { Sidebar } from './Sidebar'

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Sidebar />
    </MemoryRouter>,
  )
}

describe('Sidebar', () => {
  it('marks New request as the current page on the start page', () => {
    renderAt('/')

    expect(screen.getByRole('link', { name: 'New request' }).getAttribute('aria-current')).toBe('page')
    expect(screen.getByRole('link', { name: 'Requests' }).getAttribute('aria-current')).toBeNull()
  })

  it('keeps Requests current while a single request is open', () => {
    renderAt('/requests/abc')

    expect(screen.getByRole('link', { name: 'Requests' }).getAttribute('aria-current')).toBe('page')
  })

  it('links to the observability page', () => {
    renderAt('/observability')

    expect(screen.getByRole('link', { name: 'Observability' }).getAttribute('href')).toBe('/observability')
  })
})
