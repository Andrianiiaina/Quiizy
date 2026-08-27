import { apiClient } from '@/lib/api-client'
import type { Assignment } from '@/types/lms'

export const assignmentsApi = {
  list: (): Promise<Assignment[]> =>
    apiClient.get('/assignments').then(r => r.data),
  create: (data: { user_id: string; target_type: string; target_id: string; due_date?: string }): Promise<Assignment> =>
    apiClient.post('/assignments', data).then(r => r.data),
  cancel: (id: string): Promise<void> =>
    apiClient.delete(`/assignments/${id}`).then(() => undefined),
}
