// Session token storage. The token is a JWT; its expiry is read client-side only to
// decide whether to show the login page — the server always re-validates it.
const KEY = 'token'

export function getToken() {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  localStorage.setItem(KEY, token)
}

export function clearToken() {
  try {
    localStorage.removeItem(KEY)
  } catch {
    // storage unavailable: nothing to clear
  }
}

function expiresAt(token) {
  try {
    const payload = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(payload)).exp * 1000
  } catch {
    return 0
  }
}

export function isLoggedIn() {
  const token = getToken()
  if (token && expiresAt(token) > Date.now()) return true
  if (token) clearToken()
  return false
}
