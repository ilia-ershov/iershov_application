const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })

export function formatDate(iso) {
  return iso ? dateFormat.format(new Date(iso)) : ''
}

// "https://github.com/" -> "github.com" for display
export function displayUrl(url) {
  return url.replace(/^https?:\/\//i, '').replace(/\/$/, '')
}

export function isHttpUrl(url) {
  return /^https?:\/\//i.test(url || '')
}

export function matchesQuery(alias, query) {
  const q = query.trim().toLowerCase()
  if (!q) return true
  return [alias.address, alias.service, alias.service_url].some((value) => value.toLowerCase().includes(q))
}
