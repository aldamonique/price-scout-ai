import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import type { Market } from '../../api/types'
import { EMPTY_DRAFT, type RequestDraft } from './draft'
import { RequestComposer } from './RequestComposer'

const MARKETS: Market[] = [
  { country: 'br', language: 'pt-br', currency: 'BRL' },
  { country: 'pt', language: 'pt-pt', currency: 'EUR' },
]

function Harness({ onSubmit = () => {}, error = null }: { onSubmit?: () => void; error?: string | null }) {
  const [draft, setDraft] = useState<RequestDraft>(EMPTY_DRAFT)
  return (
    <RequestComposer
      draft={draft}
      markets={MARKETS}
      submitting={false}
      error={error}
      onChange={setDraft}
      onSubmit={onSubmit}
    />
  )
}

function runButton(): HTMLButtonElement {
  return screen.getByRole('button', { name: 'Run request' }) as HTMLButtonElement
}

describe('RequestComposer', () => {
  it('can run with only a description, because the budget is optional', () => {
    render(<Harness />)

    expect(runButton().disabled).toBe(true)
    expect(screen.getByText('Describe what you need to start.')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('What do you want to buy?'), {
      target: { value: 'A sofa for a small living room' },
    })

    expect(runButton().disabled).toBe(false)
  })

  it('refuses a budget that is not a positive number', () => {
    render(<Harness />)
    fireEvent.change(screen.getByLabelText('What do you want to buy?'), {
      target: { value: 'A sofa for a small living room' },
    })

    fireEvent.change(screen.getByLabelText('Budget (BRL, optional)'), { target: { value: 'abc' } })

    expect(runButton().disabled).toBe(true)
    expect(screen.getByText('The budget must be a number above zero, or empty.')).toBeTruthy()
  })

  it('fills the text and the budget from an example', () => {
    const onSubmit = vi.fn()
    render(<Harness onSubmit={onSubmit} />)

    fireEvent.click(screen.getByRole('button', { name: 'Home office' }))
    fireEvent.submit(runButton().closest('form')!)

    expect((screen.getByLabelText('What do you want to buy?') as HTMLTextAreaElement).value).toContain('home office')
    expect((screen.getByLabelText('Budget (BRL, optional)') as HTMLInputElement).value).toBe('2500')
    expect(onSubmit).toHaveBeenCalledOnce()
  })

  it('shows the budget in the currency of the chosen country', () => {
    render(<Harness />)

    fireEvent.change(screen.getByLabelText('Country'), { target: { value: 'pt' } })

    expect(screen.getByLabelText('Budget (EUR, optional)')).toBeTruthy()
    expect(screen.getByText('€')).toBeTruthy()
  })

  it('keeps the preferences folded until asked, then counts the ones set', () => {
    render(<Harness />)
    const toggle = screen.getByRole('button', { name: /Preferences/ })

    expect(screen.queryByLabelText('Colors')).toBeNull()
    fireEvent.click(toggle)
    fireEvent.change(screen.getByLabelText('Colors'), { target: { value: 'gray' } })

    expect(toggle.getAttribute('aria-expanded')).toBe('true')
    expect(screen.getByText('1 set')).toBeTruthy()
  })

  it('shows an error from the API', () => {
    render(<Harness error="Could not send the request: offline" />)

    expect(screen.getByRole('alert').textContent).toContain('offline')
  })
})
