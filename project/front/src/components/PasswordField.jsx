import { useId, useState } from 'react'
import { PASSWORD_RULES } from '../validation'

// Password input with a show/hide toggle and, for new passwords, a live rules checklist.
export default function PasswordField({ label, value, onChange, autoComplete = 'new-password', showRules = false, required = true }) {
  const id = useId()
  const [visible, setVisible] = useState(false)

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div className="input-row">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          required={required}
          aria-describedby={showRules ? `${id}-rules` : undefined}
        />
        <button type="button" className="button button-ghost" onClick={() => setVisible((v) => !v)}>
          {visible ? 'Скрыть' : 'Показать'}
        </button>
      </div>
      {showRules && (
        <ul id={`${id}-rules`} className="rules">
          {PASSWORD_RULES.map((rule) => {
            const ok = value.length > 0 && rule.test(value)
            return (
              <li key={rule.label} className={ok ? 'rule rule-ok' : 'rule'}>
                <span aria-hidden="true">{ok ? '✓' : '•'}</span> {rule.label}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
