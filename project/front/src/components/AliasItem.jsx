import { useId, useState } from 'react'
import { displayUrl, formatDate, isHttpUrl } from '../format'
import { errorMessage } from '../messages'
import CopyButton from './CopyButton'
import Notice from './Notice'

// One alias row. With `onSave` the service name and link can be edited in place.
export default function AliasItem({ alias, onSave, children }) {
  const id = useId()
  const [editing, setEditing] = useState(false)
  const [service, setService] = useState(alias.service)
  const [url, setUrl] = useState(alias.service_url)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const startEditing = () => {
    setService(alias.service)
    setUrl(alias.service_url)
    setError('')
    setEditing(true)
  }

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onSave(alias, { service: service.trim(), service_url: url.trim() })
      setEditing(false)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <li className={alias.active ? 'alias' : 'alias alias-inactive'}>
      <div className="alias-main">
        <div className="alias-address">
          <code>{alias.address}</code>
          <CopyButton text={alias.address} />
        </div>

        {editing ? (
          <form className="alias-edit" onSubmit={save}>
            <div className="field">
              <label htmlFor={`${id}-service`}>Сервис</label>
              <input id={`${id}-service`} value={service} maxLength={100} onChange={(e) => setService(e.target.value)} required />
            </div>
            <div className="field">
              <label htmlFor={`${id}-url`}>Ссылка на сервис</label>
              <input id={`${id}-url`} value={url} maxLength={2048} placeholder="https://example.com" onChange={(e) => setUrl(e.target.value)} />
            </div>
            <Notice>{error}</Notice>
            <div className="actions">
              <button type="submit" className="button button-primary button-small" disabled={busy}>
                Сохранить
              </button>
              <button type="button" className="button button-small" onClick={() => setEditing(false)} disabled={busy}>
                Отмена
              </button>
            </div>
          </form>
        ) : (
          <div className="alias-service">
            <span>{alias.service}</span>
            {isHttpUrl(alias.service_url) && (
              <a href={alias.service_url} target="_blank" rel="noopener noreferrer">
                {displayUrl(alias.service_url)}
              </a>
            )}
          </div>
        )}

        <div className="alias-meta">
          Создан {formatDate(alias.created_at)}
          {alias.deactivated_at && ` · отключён ${formatDate(alias.deactivated_at)}`}
        </div>
      </div>

      {!editing && (
        <div className="alias-actions">
          {onSave && (
            <button type="button" className="button button-small" onClick={startEditing}>
              Изменить
            </button>
          )}
          {children}
        </div>
      )}
    </li>
  )
}
