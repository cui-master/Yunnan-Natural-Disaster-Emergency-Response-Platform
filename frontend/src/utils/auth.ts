const TOKEN_KEY = 'ydr_token'
const USER_KEY = 'ydr_user'

export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY)

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const saveUser = (user: unknown): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export const getSavedUser = <T = unknown>(): T | null => {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}
