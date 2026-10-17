import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="card card-narrow">
      <h1>Страница не найдена</h1>
      <p className="muted">Возможно, ссылка устарела или в адресе опечатка.</p>
      <Link to="/" className="button">
        На главную
      </Link>
    </section>
  )
}
