import axios from 'axios'
import { APP_CONFIG } from '@/app/config'

export const apiClient = axios.create({
  baseURL: APP_CONFIG.apiBaseUrl,
  withCredentials: true,   // nécessaire pour les cookies HttpOnly (auth)
  headers: {
    'Content-Type': 'application/json',
  },
})

// Les intercepteurs d'erreurs seront ajoutés au module auth (Phase 2)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error),
)
