import { apiClient } from '@/lib/api-client'
import type { User } from '@/types/auth'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
}

export const authApi = {
  register: (data: RegisterRequest): Promise<User> =>
    apiClient.post<User>('/auth/register', data).then((r) => r.data),

  login: (data: LoginRequest): Promise<User> =>
    apiClient.post<User>('/auth/login', data).then((r) => r.data),

  logout: (): Promise<void> =>
    apiClient.post('/auth/logout').then(() => undefined),

  me: (): Promise<User> =>
    apiClient.get<User>('/auth/me').then((r) => r.data),

  refresh: (): Promise<User> =>
    apiClient.post<User>('/auth/refresh').then((r) => r.data),
}
