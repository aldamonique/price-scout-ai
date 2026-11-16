import type { EvalRun } from '../../api/types'

export function glossaryEffect(runs: EvalRun[]): { with: EvalRun; without: EvalRun } | null {
  const complete = runs.filter((run) => run.failed_cases === 0)
  const withGlossary = complete.find((run) => run.glossary)
  if (!withGlossary) return null
  const without = complete.find(
    (run) =>
      !run.glossary &&
      run.prompt_version === withGlossary.prompt_version &&
      run.judge_model === withGlossary.judge_model,
  )
  return without ? { with: withGlossary, without } : null
}
