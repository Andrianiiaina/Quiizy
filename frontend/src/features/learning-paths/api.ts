import { apiClient } from '@/lib/api-client'
import type { LearningPath, LPCourseItem } from '@/types/lms'
import type { PaginatedResponse } from '@/types/api'

export const lpApi = {
  list: (p?: { page?: number }): Promise<PaginatedResponse<LearningPath>> =>
    apiClient.get('/learning-paths', { params: p }).then(r => r.data),
  get: (id: string): Promise<LearningPath> =>
    apiClient.get(`/learning-paths/${id}`).then(r => r.data),
  getCourses: (id: string): Promise<LPCourseItem[]> =>
    apiClient.get(`/learning-paths/${id}/courses`).then(r => r.data),
  create: (data: { title: string; description?: string }): Promise<LearningPath> =>
    apiClient.post('/learning-paths', data).then(r => r.data),
  update: (id: string, data: Partial<{ title: string; description: string }>): Promise<LearningPath> =>
    apiClient.patch(`/learning-paths/${id}`, data).then(r => r.data),
  delete: (id: string): Promise<void> =>
    apiClient.delete(`/learning-paths/${id}`).then(() => undefined),
  publish: (id: string): Promise<LearningPath> =>
    apiClient.patch(`/learning-paths/${id}/publish`).then(r => r.data),
  archive: (id: string): Promise<LearningPath> =>
    apiClient.patch(`/learning-paths/${id}/archive`).then(r => r.data),
  addCourse: (id: string, course_id: string): Promise<void> =>
    apiClient.post(`/learning-paths/${id}/courses`, { course_id }).then(() => undefined),
  removeCourse: (id: string, course_id: string): Promise<void> =>
    apiClient.delete(`/learning-paths/${id}/courses/${course_id}`).then(() => undefined),
}
