import { apiClient } from '@/lib/api-client'
import type { AttemptResult, GenerationJob, Quiz, QuizAttempt } from '@/types/lms'

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
