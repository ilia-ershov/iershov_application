import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { aliasApi } from '../api'
import CopyButton from '../components/CopyButton'
import Notice from '../components/Notice'
import { MAIL_DOMAIN } from '../config'
import { errorMessage } from '../messages'

export default function CreateAlias() {
  const navigate = useNavigate()
  const [generated, setGenerated] = useState(null) // { alias, address, alias_token }
  const [service, setService] = useState('')
  const [serviceUrl, setServiceUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const generate = async () => {
    setError('')
    setBusy(true)
    try {
      setGenerated(await aliasApi.generate())
    } catch (err) {
      setError(errorMessage(err, 'Не удалось получить адрес.'))
    } finally {
      setBusy(false)
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    if (!generated) {
      setError('Сначала получите адрес.')
      return
    }
    setError('')
    setBusy(true)
    try {
      const { alias } = await aliasApi.create({
        alias_token: generated.alias_token,
        service: service.trim(),
        service_url: serviceUrl.trim(),
      })
      navigate('/dashboard', { state: { created: alias.address } })
    } catch (err) {
      setError(errorMessage(err, 'Не удалось создать адрес.'))
      if (['invalid_alias_token', 'alias_taken'].includes(err.response?.data?.code)) setGenerated(null)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card card-narrow">
      <h1>Новый адрес</h1>
      <p className="muted">
        Адрес генерируется случайно: по нему нельзя догадаться, кому он принадлежит, и связать ваши аккаунты на разных
        сайтах.
      </p>

      <form onSubmit={submit} className="form">
        <div className="field">
          <span className="label">Адрес</span>
          <div className="generated">
            <code>{generated ? generated.address : `xxxxxxxxxx@${MAIL_DOMAIN}`}</code>
            {generated && <CopyButton text={generated.address} />}
          </div>
          <button type="button" className="button" onClick={generate} disabled={busy}>
            {generated ? 'Сгенерировать другой' : 'Получить адрес'}
          </button>
        </div>

        <div className="field">
          <label htmlFor="service">Сервис, для которого этот адрес</label>
          <input id="service" value={service} maxLength={100} placeholder="Например, GitHub" onChange={(e) => setService(e.target.value)} required />
        </div>

        <div className="field">
          <label htmlFor="service-url">Ссылка на сервис (необязательно)</label>
          <input
            id="service-url"
            value={serviceUrl}
            maxLength={2048}
            placeholder="https://github.com"
            onChange={(e) => setServiceUrl(e.target.value)}
          />
        </div>

        <Notice>{error}</Notice>

        <div className="actions">
          <button type="submit" className="button button-primary" disabled={busy || !generated}>
            Создать
          </button>
          <Link to="/dashboard" className="button button-ghost">
            Отмена
          </Link>
        </div>
      </form>
    </section>
  )
}
