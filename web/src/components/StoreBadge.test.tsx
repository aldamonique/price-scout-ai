import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { colorFor } from '../lib/storeColor'
import { StoreBadge } from './StoreBadge'

describe('StoreBadge', () => {
  it('shows the store icon when there is one', () => {
    render(<StoreBadge store="Mobly" icon="https://icons.example/mobly.png" />)

    expect(screen.getByRole('img', { name: 'Mobly' }).tagName).toBe('IMG')
  })

  it('shows the initial when there is no icon', () => {
    render(<StoreBadge store="lar & estilo" icon={null} />)

    expect(screen.getByRole('img', { name: 'lar & estilo' }).textContent).toBe('L')
  })

  it('falls back to the initial when the icon fails to load', () => {
    render(<StoreBadge store="Mobly" icon="https://broken.example/x.png" />)

    fireEvent.error(screen.getByRole('img', { name: 'Mobly' }))

    expect(screen.getByRole('img', { name: 'Mobly' }).textContent).toBe('M')
  })

  it('gives the same store the same color every time', () => {
    expect(colorFor('Mobly')).toBe(colorFor('Mobly'))
  })
})
