import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api'
import { setToken } from '../auth'
import EmailVerificationField from '../components/EmailVerificationField'
import Notice from '../components/Notice'
import PasswordField from '../components/PasswordField'
import { errorMessage } from '../messages'
import { isStrongPassword, PASSWORD_HINT } from '../validation'

export default function Signup() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [verificationToken, setVerificationToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const changeEmail = (value) => {
    setEmail(value)
    setVerificationToken('') // a verification is only valid for the address it was made for
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!verificationToken) return setError('Подтвердите адрес электронной почты.')
    if (!isStrongPassword(password)) return setError(PASSWORD_HINT)
    if (password !== confirm) return setError('Пароли не совпадают.')

    setBusy(true)
    try {
      const result = await authApi.register({
        name: name.trim(),
        email: email.trim(),
        password,
        verification_token: verificationToken,
      })
      setToken(result.token)
      navigate('/dashboard', { replace: true })
    } catch (err) {
      setError(errorMessage(err, 'Не удалось создать аккаунт.'))
      if (err.response?.data?.code === 'invalid_verification') setVerificationToken('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card card-narrow">
      <h1>Регистрация</h1>
      <p className="muted">На основной адрес будут пересылаться письма со всех ваших адресов.</p>
      <form onSubmit={submit} className="form">
        <div className="field">
          <label htmlFor="name">Имя</label>
          <input id="name" autoComplete="name" value={name} maxLength={100} onChange={(e) => setName(e.target.value)} required />
        </div>
        <EmailVerificationField
          label="Основной адрес"
          purpose="register"
          email={email}
          onEmailChange={changeEmail}
          token={verificationToken}
          onVerified={setVerificationToken}
        />
        <PasswordField label="Пароль" value={password} onChange={setPassword} showRules />
        <PasswordField label="Повторите пароль" value={confirm} onChange={setConfirm} />
        <Notice>{error}</Notice>
        <button type="submit" className="button button-primary button-wide" disabled={busy}>
          Создать аккаунт
        </button>
      </form>
      <p className="form-links">
        <Link to="/login">Уже есть аккаунт? Войти</Link>
      </p>
    </section>
  )
}
