// Client-side checks for instant feedback; the backend enforces the same rules.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function isEmail(value) {
  return EMAIL_RE.test(value.trim())
}

export const PASSWORD_RULES = [
  { label: 'не короче 8 символов', test: (p) => p.length >= 8 },
  { label: 'строчная буква', test: (p) => /[a-z]/.test(p) },
  { label: 'заглавная буква', test: (p) => /[A-Z]/.test(p) },
  { label: 'цифра', test: (p) => /\d/.test(p) },
  { label: 'спецсимвол (!, ?, -, # …)', test: (p) => /[^A-Za-z0-9]/.test(p) },
  // bcrypt only uses the first 72 bytes of a password
  { label: 'не длиннее 72 байт', test: (p) => new TextEncoder().encode(p).length <= 72 },
]

export const PASSWORD_HINT =
  'Пароль должен быть не короче 8 символов и содержать строчную и заглавную латинские буквы, цифру и спецсимвол.'

export function isStrongPassword(password) {
  return PASSWORD_RULES.every((rule) => rule.test(password))
}
