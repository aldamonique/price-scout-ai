import { act, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError } from '../../api/client'
import type { RequestStatus } from '../../api/types'
import { DeleteRequestButton } from './DeleteRequestButton'

function renderButton(status: RequestStatus = 'done') {
  render(
    <MemoryRouter initialEntries={['/requests/r1']}>
      <Routes>
        <Route path="/requests/r1" element={<DeleteRequestButton requestId="r1" status={status} />} />
        <Route path="/requests" element={<p>Request list</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('DeleteRequestButton', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('asks before deleting and goes back to the list after', async () => {
    const deleteRequest = vi.spyOn(api, 'deleteRequest').mockResolvedValue(undefined)
    renderButton()

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    expect(screen.getByText('Delete this request?')).toBeTruthy()
    expect(deleteRequest).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    await act(async () => {})

    expect(deleteRequest).toHaveBeenCalledWith('r1')
    expect(screen.getByText('Request list')).toBeTruthy()
  })

  it('can be cancelled', () => {
    const deleteRequest = vi.spyOn(api, 'deleteRequest')
    renderButton()

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(deleteRequest).not.toHaveBeenCalled()
    expect(screen.queryByText('Delete this request?')).toBeNull()
  })

  it('is disabled while the request is running', () => {
    renderButton('running')

    expect((screen.getByRole('button', { name: 'Delete' }) as HTMLButtonElement).disabled).toBe(true)
  })

  it('shows the error when the API refuses', async () => {
    vi.spyOn(api, 'deleteRequest').mockRejectedValue(new ApiError(409, 'This request is still running.'))
    renderButton()

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))
    await act(async () => {})

    expect(screen.getByRole('alert').textContent).toBe('This request is still running.')
  })
})
