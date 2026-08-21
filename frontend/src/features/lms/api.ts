import { apiClient } from '@/lib/api-client'
import type {
  Assignment, AttemptResult, Enrollment, ContentProgress,
  GenerationJob, LearningPath, LPCourseItem, Quiz, QuizAttempt,
} from '@/types/lms'
import type { PaginatedResponse } from '@/types/api'

export const lpApi = {
  list: (p?: { page?: number }): Promise<PaginatedResponse<LearningPath>> =>
    apiClient.get('/learning-paths', { params: p }).then(r => r.data),
  get: (id: string): Promise<LearningPath> => apiClient.get(`/learning-paths/${id}`).then(r => r.data),
  getCourses: (id: string): Promise<LPCourseItem[]> => apiClient.get(`/learning-paths/${id}/courses`).then(r => r.data),
  create: (data: { title: string; description?: string }): Promise<LearningPath> =>
    apiClient.post('/learning-paths', data).then(r => r.data),
  update: (id: string, data: Partial<{ title: string; description: string }>): Promise<LearningPath> =>
    apiClient.patch(`/learning-paths/${id}`, data).then(r => r.data),
  delete: (id: string): Promise<void> => apiClient.delete(`/learning-paths/${id}`).then(() => undefined),
  publish: (id: string): Promise<LearningPath> => apiClient.patch(`/learning-paths/${id}/publish`).then(r => r.data),
  archive: (id: string): Promise<LearningPath> => apiClient.patch(`/learning-paths/${id}/archive`).then(r => r.data),
  addCourse: (id: string, course_id: string): Promise<void> =>
    apiClient.post(`/learning-paths/${id}/courses`, { course_id }).then(() => undefined),
  removeCourse: (id: string, course_id: string): Promise<void> =>
    apiClient.delete(`/learning-paths/${id}/courses/${course_id}`).then(() => undefined),
}

export const assignmentsApi = {
  list: (): Promise<Assignment[]> => apiClient.get('/assignments').then(r => r.data),
  create: (data: { user_id: string; target_type: string; target_id: string; due_date?: string }): Promise<Assignment> =>
    apiClient.post('/assignments', data).then(r => r.data),
  cancel: (id: string): Promise<void> => apiClient.delete(`/assignments/${id}`).then(() => undefined),
}

export const enrollmentsApi = {
  list: (): Promise<Enrollment[]> => apiClient.get('/enrollments').then(r => r.data),
  get: (id: string): Promise<Enrollment> => apiClient.get(`/enrollments/${id}`).then(r => r.data),
  getProgress: (id: string): Promise<ContentProgress[]> => apiClient.get(`/enrollments/${id}/progress`).then(r => r.data),
  updateProgress: (enrollmentId: string, contentId: string, data: { status: string; progress_percent: number }): Promise<ContentProgress> =>
    apiClient.post(`/enrollments/${enrollmentId}/contents/${contentId}/progress`, data).then(r => r.data),
}

export const quizzesApi = {
  generate: (courseId: string): Promise<GenerationJob> =>
    apiClient.post(`/courses/${courseId}/quiz/generate`).then(r => r.data),
  getJob: (jobId: string): Promise<GenerationJob> =>
    apiClient.get(`/quiz-generation-jobs/${jobId}`).then(r => r.data),
  getForCourse: (courseId: string): Promise<Quiz> =>
    apiClient.get(`/courses/${courseId}/quiz`).then(r => r.data),
  startAttempt: (quizId: string, enrollmentId: string): Promise<QuizAttempt> =>
    apiClient.post(`/quizzes/${quizId}/attempts`, null, { params: { enrollment_id: enrollmentId } }).then(r => r.data),
  submitAnswer: (attemptId: string, data: { question_id: string; selected_option_id: string }): Promise<void> =>
    apiClient.post(`/quiz-attempts/${attemptId}/answers`, data).then(() => undefined),
  complete: (attemptId: string): Promise<AttemptResult> =>
    apiClient.post(`/quiz-attempts/${attemptId}/complete`).then(r => r.data),
  getAttempts: (enrollmentId: string): Promise<unknown[]> =>
    apiClient.get(`/enrollments/${enrollmentId}/quiz-attempts`).then(r => r.data),
}
