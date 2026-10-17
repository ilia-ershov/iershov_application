import { Link, useLocation } from 'react-router-dom'
import Notice from '../components/Notice'
import { MAIL_DOMAIN } from '../config'

const FEATURES = [
  {
    title: 'Отдельный адрес для каждого сайта',
    text: 'Регистрируйтесь с адресом вида x7k2m9q4ab@' + MAIL_DOMAIN + ' — письма приходят в ваш обычный почтовый ящик.',
  },
  {
    title: 'Утечка? Просто отключите адрес',
    text: 'Если сайт начал слать спам или его базу украли, отключите адрес в один клик. Основная почта останется чистой.',
  },
  {
    title: 'Вас не найти по почте',
    text: 'Случайные адреса нельзя связать между собой, поэтому по утёкшей базе не понять, где ещё вы зарегистрированы.',
  },
  {
    title: 'Смена почты без хлопот',
    text: 'Поменяли основной ящик? Обновите его один раз в настройках, а не на каждом сайте.',
  },
]

export default function Home() {
  const location = useLocation()
  return (
    <div className="stack">
      <Notice type="success">{location.state?.message}</Notice>
      <section className="hero">
        <h1>Организатор почты</h1>
        <p className="lead">
          Скрывайте настоящий адрес электронной почты от сайтов, спамеров и фишинга. Выдаём адреса на {MAIL_DOMAIN},
          которые пересылают письма вам и отключаются по первому требованию.
        </p>
        <div className="actions actions-center">
          <Link to="/signup" className="button button-primary button-large">
            Создать аккаунт
          </Link>
          <Link to="/login" className="button button-large">
            Войти
          </Link>
        </div>
      </section>
      <section className="features">
        {FEATURES.map((feature) => (
          <article key={feature.title} className="card feature">
            <h2>{feature.title}</h2>
            <p>{feature.text}</p>
          </article>
        ))}
      </section>
    </div>
  )
}
