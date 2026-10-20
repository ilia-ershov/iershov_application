import axios from 'axios'
import { API_URL } from './config'
import { clearToken, getToken } from './auth'

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach the session token to everything except the sign-in endpoints.
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token && !config.url.startsWith('/auth/')) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// An authenticated request answered with 401 means the session expired or was revoked.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && error.config?.headers?.Authorization) {
      clearToken()
      if (window.location.pathname !== '/login') window.location.assign('/login?expired=1')
    }
    return Promise.reject(error)
  },
)

const body = (request) => request.then((response) => response.data)

export const authApi = {
  requestCode: (email, purpose) => body(api.post('/auth/request-code', { email, purpose })),
  verifyCode: (email, code, purpose) => body(api.post('/auth/verify-code', { email, code, purpose })),
  register: (payload) => body(api.post('/auth/register', payload)),
  login: (email, password) => body(api.post('/auth/login', { email, password })),
  loginSecondFactor: (mfaToken, code) => body(api.post('/auth/login/2fa', { mfa_token: mfaToken, code })),
  resetPassword: (payload) => body(api.post('/auth/reset-password', payload)),
}

export const accountApi = {
  get: () => body(api.get('/account')),
  changeEmail: (payload) => body(api.post('/account/email', payload)),
  changePassword: (payload) => body(api.post('/account/password', payload)),
  logoutEverywhere: () => body(api.post('/account/logout-all')),
  remove: (password) => body(api.delete('/account', { data: { password } })),
  setup2fa: () => body(api.post('/account/2fa/setup')),
  enable2fa: (setupToken, code) => body(api.post('/account/2fa/enable', { setup_token: setupToken, code })),
  disable2fa: (password, code) => body(api.post('/account/2fa/disable', { password, code })),
}

export const aliasApi = {
  list: (status) => body(api.get('/aliases', { params: { status } })),
  generate: () => body(api.post('/aliases/generate')),
  create: (payload) => body(api.post('/aliases', payload)),
  update: (id, payload) => body(api.patch(`/aliases/${id}`, payload)),
  deactivate: (id) => body(api.post(`/aliases/${id}/deactivate`)),
  activate: (id) => body(api.post(`/aliases/${id}/activate`)),
  remove: (id) => body(api.delete(`/aliases/${id}`)),
}
