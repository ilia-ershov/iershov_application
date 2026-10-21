import { lazy } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { GuestOnly, RequireAuth } from './components/Guards'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'

// Everything except the entry pages is loaded on demand.
const CreateAlias = lazy(() => import('./pages/CreateAlias'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Deactivated = lazy(() => import('./pages/Deactivated'))
const Help = lazy(() => import('./pages/Help'))
const NotFound = lazy(() => import('./pages/NotFound'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const Settings = lazy(() => import('./pages/Settings'))
const Signup = lazy(() => import('./pages/Signup'))

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/help" element={<Help />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route element={<GuestOnly />}>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Route>
          <Route element={<RequireAuth />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/create" element={<CreateAlias />} />
            <Route path="/deactivated" element={<Deactivated />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
