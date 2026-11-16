const KEY = 'price-scout.admin-token'

export function readAdminToken(): string | null {
  try {
    return window.localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function saveAdminToken(token: string): void {
  try {
    if (token.trim()) window.localStorage.setItem(KEY, token.trim())
    else window.localStorage.removeItem(KEY)
  } catch {
    return
  }
}
