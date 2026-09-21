/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
    },
  },

  // Proxy vers le backend — cible surchargeable via VITE_PROXY_TARGET :
  // "http://localhost:8000" en dev local (npm run dev sur l'hôte),
  // "http://backend:8000" en dev Docker (voir docker-compose.override.yml).
  // En build de production, c'est nginx qui gère le proxy — cette config ne s'applique pas.
  server: {
    port: 5175,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    css: true,
  },
})
