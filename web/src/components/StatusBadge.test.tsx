import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it.each([
    ['queued', 'Queued'],
    ['running', 'Running'],
    ['done', 'Done'],
    ['failed', 'Failed'],
  ] as const)('labels %s as %s', (status, label) => {
    render(<StatusBadge status={status} />)

    expect(screen.getByText(label)).toBeTruthy()
  })
})
