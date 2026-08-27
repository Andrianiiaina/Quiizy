import { apiClient } from '@/lib/api-client'
import type { ContentProgress, Enrollment } from '@/types/lms'

export const enrollmentsApi = {
  list: (): Promise<Enrollment[]> =>
    apiClient.get('/enrollments').then(r => r.data),
  get: (id: string): Promise<Enrollment> =>
    apiClient.get(`/enrollments/${id}`).then(r => r.data),
  getProgress: (id: string): Promise<ContentProgress[]> =>
    apiClient.get(`/enrollments/${id}/progress`).then(r => r.data),
  updateProgress: (
    enrollmentId: string,
    contentId: string,
    data: { status: string; progress_percent: number },
  ): Promise<ContentProgress> =>
    apiClient.post(`/enrollments/${enrollmentId}/contents/${contentId}/progress`, data).then(r => r.data),
}
