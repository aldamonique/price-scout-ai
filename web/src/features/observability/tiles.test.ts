import { describe, expect, it } from 'vitest'

import { OVERVIEW } from '../../test/fixtures'
import { overviewTiles } from './tiles'

describe('overviewTiles', () => {
  it('turns the overview into six headline tiles, cost first and highlighted', () => {
    const tiles = overviewTiles(OVERVIEW)

    expect(tiles.map((tile) => tile.label)).toEqual([
      'Total cost',
      'Success rate',
      'Request duration',
      'Model calls',
      'Tokens',
      'Call error rate',
    ])
    expect(tiles.filter((tile) => tile.highlight).map((tile) => tile.label)).toEqual(['Total cost'])
    expect(tiles.map((tile) => tile.value)).toEqual(['$0.27', '75%', '92.4 s', '40', '138K', '5%'])
  })

  it('shows dashes before anything ran', () => {
    const empty = {
      ...OVERVIEW,
      runs: { ...OVERVIEW.runs, success_rate: null, avg_duration_s: null, avg_cost_usd: null },
      llm: { ...OVERVIEW.llm, cost_usd: null, error_rate: null },
    }

    const values = overviewTiles(empty).map((tile) => tile.value)

    expect(values[0]).toBe('—')
    expect(values[1]).toBe('—')
    expect(values[2]).toBe('—')
  })
})
