import { useState } from 'react'

export default function CopyButton({ text, label = 'Копировать', className = 'button button-small' }) {
  const [state, setState] = useState('idle')

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setState('done')
    } catch {
      setState('failed') // clipboard API needs https or localhost
    }
    setTimeout(() => setState('idle'), 2000)
  }

  return (
    <button type="button" className={className} onClick={copy}>
      {state === 'done' ? 'Скопировано' : state === 'failed' ? 'Не удалось' : label}
    </button>
  )
}
