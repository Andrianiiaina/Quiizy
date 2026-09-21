import { apiClient } from '@/lib/api-client'
import type { User } from '@/types/auth'

export const usersApi = {
  list: (): Promise<User[]> =>
    apiClient.get<User[]>('/users').then((r) => r.data),

  get: (id: string): Promise<User> =>
    apiClient.get<User>(`/users/${id}`).then((r) => r.data),
}
