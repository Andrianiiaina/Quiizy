import { apiClient } from '@/lib/api-client'
import { APP_CONFIG } from '@/app/config'
import type { CourseContent, CreateContentRequest, FileAsset } from '@/types/content'

export const contentsApi = {
  listForCourse: (courseId: string): Promise<CourseContent[]> =>
    apiClient.get<CourseContent[]>(`/courses/${courseId}/contents`).then((r) => r.data),

  get: (id: string): Promise<CourseContent> =>
    apiClient.get<CourseContent>(`/contents/${id}`).then((r) => r.data),

  create: (courseId: string, data: CreateContentRequest): Promise<CourseContent> =>
    apiClient.post<CourseContent>(`/courses/${courseId}/contents`, data).then((r) => r.data),

  update: (id: string, data: Partial<CreateContentRequest>): Promise<CourseContent> =>
    apiClient.patch<CourseContent>(`/contents/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/contents/${id}`).then(() => undefined),

  reorder: (courseId: string, items: { id: string; position: number }[]): Promise<void> =>
    apiClient.patch(`/courses/${courseId}/contents/reorder`, items).then(() => undefined),
}

export const filesApi = {
  upload: (file: File): Promise<FileAsset> => {
    const form = new FormData()
    form.append('file', file)
    return apiClient
      .post<FileAsset>('/files/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then((r) => r.data)
  },
  // Returns a URL the browser can use to download — auth cookie is sent automatically
  downloadUrl: (id: string): string => `${APP_CONFIG.apiBaseUrl}/files/${id}`,
}
