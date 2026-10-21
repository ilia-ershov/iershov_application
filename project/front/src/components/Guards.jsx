import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { isLoggedIn } from '../auth'

// Pages that need a session: send visitors to the login page and back afterwards.
export function RequireAuth() {
  const location = useLocation()
  if (!isLoggedIn()) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

// Login/signup pages make no sense with an active session.
export function GuestOnly() {
  if (isLoggedIn()) return <Navigate to="/dashboard" replace />
  return <Outlet />
}
