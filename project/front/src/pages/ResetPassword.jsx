import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../api'
import { clearToken } from '../auth'
import EmailVerificationField from '../components/EmailVerificationField'
import Notice from '../components/Notice'
import PasswordField from '../components/PasswordField'
import { errorMessage } from '../messages'
import { isStrongPassword, PASSWORD_HINT } from '../validation'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [verificationToken, setVerificationToken] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const changeEmail = (value) => {
    setEmail(value)
    setVerificationToken('')
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!verificationToken) return setError('Подтвердите адрес электронной почты.')
    if (!isStrongPassword(password)) return setError(PASSWORD_HINT)
    if (password !== confirm) return setError('Пароли не совпадают.')

    setBusy(true)
    try {
      await authApi.resetPassword({ email: email.trim(), password, verification_token: verificationToken })
      clearToken() // every session was signed out by the reset
      navigate('/login', { replace: true, state: { message: 'Пароль изменён. Войдите с новым паролем.' } })
    } catch (err) {
      setError(errorMessage(err, 'Не удалось изменить пароль.'))
      if (err.response?.data?.code === 'invalid_verification') setVerificationToken('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="card card-narrow">
      <h1>Восстановление пароля</h1>
      <p className="muted">
        Мы отправим код на основной адрес аккаунта. После смены пароля все сеансы будут завершены. Если включена
        двухфакторная аутентификация, при входе по-прежнему понадобится код из приложения.
      </p>
      <form onSubmit={submit} className="form">
        <EmailVerificationField
          label="Основной адрес"
          purpose="reset_password"
          email={email}
          onEmailChange={changeEmail}
          token={verificationToken}
          onVerified={setVerificationToken}
        />
        {verificationToken && (
          <>
            <PasswordField label="Новый пароль" value={password} onChange={setPassword} showRules />
            <PasswordField label="Повторите пароль" value={confirm} onChange={setConfirm} />
          </>
        )}
        <Notice>{error}</Notice>
        <button type="submit" className="button button-primary button-wide" disabled={busy || !verificationToken}>
          Сменить пароль
        </button>
      </form>
      <p className="form-links">
        <Link to="/login">Вспомнили пароль? Войти</Link>
      </p>
    </section>
  )
}
