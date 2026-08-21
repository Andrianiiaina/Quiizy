import { apiClient } from '@/lib/api-client'
import type { Category } from '@/types/course'

export const categoriesApi = {
  list: (): Promise<Category[]> =>
    apiClient.get<Category[]>('/categories').then((r) => r.data),
}
