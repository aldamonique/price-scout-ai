import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { evalRun } from '../../test/fixtures'
import { glossaryEffect } from './glossaryEffect'
import { JudgeAccuracy } from './JudgeAccuracy'

const WITH = evalRun()
const WITHOUT = evalRun({
  run_id: 'run-plain',
  glossary: false,
  decision_accuracy: 0.8,
  discard: { precision: 0.7, recall: 0.7, f1: 0.7 },
  grouping: { precision: 0.85, recall: 0.85, f1: 0.85 },
})

describe('JudgeAccuracy', () => {
  it('pairs the latest run with and without the glossary of the same judge', () => {
    expect(glossaryEffect([WITH, WITHOUT])?.without.run_id).toBe('run-plain')
    expect(glossaryEffect([WITH, { ...WITHOUT, prompt_version: 'v1' }])).toBeNull()
    expect(glossaryEffect([WITHOUT])).toBeNull()
  })

  it('leaves runs with failed cases out of the glossary effect and flags them', () => {
    const broken = evalRun({ run_id: 'run-broken', failed_cases: 2 })

    expect(glossaryEffect([broken, WITHOUT])).toBeNull()
    render(<JudgeAccuracy runs={[broken, WITHOUT]} />)
    expect(screen.getByText('2 failed')).toBeTruthy()
  })

  it('shows the glossary effect in points and one row per run', () => {
    render(<JudgeAccuracy runs={[WITH, WITHOUT]} />)

    expect(screen.getByText('+12 pts')).toBeTruthy()
    expect(screen.getByText('+20 pts')).toBeTruthy()
    expect(screen.getAllByRole('row')).toHaveLength(3)
  })

  it('explains how to run the first evaluation', () => {
    render(<JudgeAccuracy runs={[]} />)

    expect(screen.getByText(/No evaluation yet/)).toBeTruthy()
  })
})
