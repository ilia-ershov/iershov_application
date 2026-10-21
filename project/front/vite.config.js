import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // The browser talks to /api on the same origin; Vite forwards it to Flask during development.
  const proxy = { '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:5000' } }
  // The dev server is for development only; production serves the built `dist/` (see nginx.conf).
  const allowedHosts = env.DEV_ALLOWED_HOSTS ? env.DEV_ALLOWED_HOSTS.split(',') : []

  return {
    plugins: [react()],
    server: { proxy, allowedHosts },
    preview: { proxy },
  }
})
