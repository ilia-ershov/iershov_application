import { useEffect, useState } from 'react'
import { aliasApi } from '../api'
import AliasItem from '../components/AliasItem'
import Notice from '../components/Notice'
import SearchBox from '../components/SearchBox'
import { matchesQuery } from '../format'
import { errorMessage } from '../messages'

export default function Deactivated() {
  const [aliases, setAliases] = useState(null)
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let cancelled = false
    aliasApi
      .list('inactive')
      .then((list) => !cancelled && setAliases(list.aliases))
      .catch((err) => {
        if (cancelled) return
        setError(errorMessage(err, 'Не удалось загрузить адреса.'))
        setAliases([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  const activate = async (alias) => {
    if (!window.confirm(`Включить ${alias.address} снова? Письма на него опять будут пересылаться вам.`)) return
    setError('')
    try {
      await aliasApi.activate(alias.id)
      setAliases((list) => list.filter((item) => item.id !== alias.id))
      setNotice(`Адрес ${alias.address} снова активен.`)
    } catch (err) {
      setError(errorMessage(err, 'Не удалось включить адрес.'))
    }
  }

  const visible = (aliases || []).filter((alias) => matchesQuery(alias, query))

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Отключённые адреса</h1>
          <p className="muted">
            Письма на эти адреса не принимаются. Адреса закреплены за вами и никогда не будут выданы другому
            пользователю.
          </p>
        </div>
      </div>

      <Notice type="success">{notice}</Notice>
      <Notice>{error}</Notice>

      {aliases === null ? (
        <p className="muted">Загрузка…</p>
      ) : aliases.length === 0 ? (
        <div className="empty">
          <p>Отключённых адресов нет.</p>
        </div>
      ) : (
        <>
          {aliases.length > 5 && <SearchBox value={query} onChange={setQuery} />}
          <ul className="alias-list">
            {visible.map((alias) => (
              <AliasItem key={alias.id} alias={alias}>
                <button type="button" className="button button-small" onClick={() => activate(alias)}>
                  Включить снова
                </button>
              </AliasItem>
            ))}
          </ul>
          {visible.length === 0 && <p className="muted">Ничего не найдено.</p>}
        </>
      )}
    </section>
  )
}
