import { apiClient } from '@/lib/api-client'
import type { Category } from '@/types/course'

export const categoriesApi = {
  list: (): Promise<Category[]> =>
    apiClient.get<Category[]>('/categories').then((r) => r.data),

  create: (data: { name: string; description?: string | null }): Promise<Category> =>
    apiClient.post<Category>('/categories', data).then((r) => r.data),
}
