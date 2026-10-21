import { MAIL_DOMAIN } from './config'
import { PASSWORD_HINT } from './validation'

// User-facing texts for the API's machine-readable error codes.
const MESSAGES = {
  invalid_request: 'Некорректный запрос.',
  invalid_field: 'Проверьте правильность заполнения полей.',
  invalid_email: 'Введите действительный адрес электронной почты.',
  alias_domain_email: `Адрес на ${MAIL_DOMAIN} нельзя сделать основным: укажите внешний почтовый ящик.`,
  weak_password: PASSWORD_HINT,
  email_taken: 'Аккаунт с таким адресом уже существует.',
  invalid_credentials: 'Неверная почта или пароль.',
  invalid_code: 'Неверный или просроченный код.',
  too_many_attempts: 'Слишком много неверных попыток. Запросите новый код.',
  resend_too_soon: 'Код уже отправлен. Новый можно запросить чуть позже.',
  mail_unavailable: 'Не удалось отправить письмо. Попробуйте позже.',
  invalid_verification: 'Адрес не подтверждён или подтверждение устарело. Запросите новый код.',
  invalid_password: 'Неверный пароль.',
  invalid_alias_token: 'Полученный адрес устарел. Получите новый адрес.',
  alias_taken: 'Этот адрес уже использован. Получите новый адрес.',
  alias_limit: 'Достигнут лимит адресов. Отключённые адреса тоже учитываются: ненужные можно удалить в разделе «Отключённые».',
  alias_active: 'Сначала отключите адрес.',
  alias_unavailable: 'Не удалось подобрать адрес. Попробуйте ещё раз.',
  invalid_url: 'Укажите ссылку вида https://example.com.',
  not_found: 'Адрес не найден.',
  mfa_expired: 'Время на вход истекло. Войдите заново.',
  invalid_mfa_code: 'Неверный код из приложения или код восстановления.',
  invalid_setup_token: 'Настройка устарела. Начните заново.',
  mfa_already_enabled: 'Двухфакторная аутентификация уже включена.',
  rate_limited: 'Слишком много попыток. Подождите немного и попробуйте снова.',
  payload_too_large: 'Слишком длинные данные.',
  internal_error: 'Ошибка сервера. Попробуйте позже.',
}

export function errorMessage(error, fallback = 'Что-то пошло не так. Попробуйте ещё раз.') {
  if (!error?.response) return 'Нет связи с сервером. Проверьте подключение и попробуйте снова.'
  const data = error.response.data || {}
  let text = MESSAGES[data.code] || fallback
  if (data.code === 'invalid_code' && data.attempts_left) text += ` Осталось попыток: ${data.attempts_left}.`
  if (data.code === 'resend_too_soon' && data.retry_after) {
    text = `Код уже отправлен. Новый можно запросить через ${data.retry_after} с.`
  }
  return text
}
