const COLORS = ['#ad7189', '#ec8fb0', '#b9a2f0', '#f7b195', '#7cc6a4', '#8fb4ec']

export function colorFor(store: string): string {
  let hash = 0
  for (const char of store) {
    hash = (hash * 31 + char.charCodeAt(0)) % 9973
  }
  return COLORS[hash % COLORS.length] ?? '#ad7189'
}
