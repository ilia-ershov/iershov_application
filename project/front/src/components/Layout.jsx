import { Suspense, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { clearToken, isLoggedIn } from '../auth'
import { MAIL_DOMAIN } from '../config'

const PRIVATE_LINKS = [
  { to: '/dashboard', label: 'Адреса' },
  { to: '/deactivated', label: 'Отключённые' },
  { to: '/settings', label: 'Настройки' },
  { to: '/help', label: 'Помощь' },
]

const PUBLIC_LINKS = [
  { to: '/help', label: 'Помощь' },
  { to: '/login', label: 'Войти' },
  { to: '/signup', label: 'Регистрация' },
]

export default function Layout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [menu, setMenu] = useState({ open: false, path: location.pathname })
  const loggedIn = isLoggedIn()
  const links = loggedIn ? PRIVATE_LINKS : PUBLIC_LINKS
  // the mobile menu closes itself on navigation
  const menuOpen = menu.open && menu.path === location.pathname

  const logout = () => {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <Link to={loggedIn ? '/dashboard' : '/'} className="brand">
            <span className="brand-mark" aria-hidden="true">@</span>
            {MAIL_DOMAIN}
          </Link>
          <button
            type="button"
            className="menu-toggle"
            aria-expanded={menuOpen}
            aria-controls="main-nav"
            aria-label="Меню"
            onClick={() => setMenu({ open: !menuOpen, path: location.pathname })}
          >
            <span />
            <span />
            <span />
          </button>
          <nav id="main-nav" className={menuOpen ? 'nav nav-open' : 'nav'}>
            {links.map((link) => (
              <NavLink key={link.to} to={link.to} className="nav-link">
                {link.label}
              </NavLink>
            ))}
            {loggedIn && (
              <button type="button" className="nav-link nav-button" onClick={logout}>
                Выйти
              </button>
            )}
          </nav>
        </div>
      </header>
      <main className="main">
        <Suspense fallback={<p className="muted">Загрузка…</p>}>
          <Outlet />
        </Suspense>
      </main>
      <footer className="footer">
        {MAIL_DOMAIN} — адреса для регистрации на сайтах без раскрытия основной почты
      </footer>
    </div>
  )
}
