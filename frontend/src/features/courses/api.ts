import { apiClient } from '@/lib/api-client'
import type { Course, CreateCourseRequest, UpdateCourseRequest } from '@/types/course'
import type { PaginatedResponse } from '@/types/api'

export const coursesApi = {
  list: (params?: { page?: number; per_page?: number }): Promise<PaginatedResponse<Course>> =>
    apiClient.get<PaginatedResponse<Course>>('/courses', { params }).then((r) => r.data),

  get: (id: string): Promise<Course> =>
    apiClient.get<Course>(`/courses/${id}`).then((r) => r.data),

  create: (data: CreateCourseRequest): Promise<Course> =>
    apiClient.post<Course>('/courses', data).then((r) => r.data),

  update: (id: string, data: UpdateCourseRequest): Promise<Course> =>
    apiClient.patch<Course>(`/courses/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/courses/${id}`).then(() => undefined),

  publish: (id: string): Promise<Course> =>
    apiClient.patch<Course>(`/courses/${id}/publish`).then((r) => r.data),

  archive: (id: string): Promise<Course> =>
    apiClient.patch<Course>(`/courses/${id}/archive`).then((r) => r.data),
}
