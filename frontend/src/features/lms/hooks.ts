import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { enrollmentsApi, lpApi, quizzesApi } from './api'
import type { ContentProgress, Enrollment, GenerationJob, LearningPath, Quiz } from '@/types/lms'

export function useLPs() {
  return useQuery<{ items: LearningPath[]; total: number; page: number; per_page: number }>({ queryKey: ['lps'], queryFn: () => lpApi.list() })
}

export function useLP(id: string) {
  return useQuery<LearningPath>({ queryKey: ['lps', id], queryFn: () => lpApi.get(id), enabled: !!id })
}

export function useLPCourses(id: string) {
  return useQuery({ queryKey: ['lps', id, 'courses'], queryFn: () => lpApi.getCourses(id), enabled: !!id })
}

export function useCreateLP() {
  const qc = useQueryClient()
  return useMutation<LearningPath, Error, Parameters<typeof lpApi.create>[0]>({
    mutationFn: lpApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['lps'] }),
  })
}

export function useUpdateLP(id: string) {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (data: Parameters<typeof lpApi.update>[1]) => lpApi.update(id, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['lps'] }) })
}

export function useDeleteLP() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: lpApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: ['lps'] }) })
}

export function usePublishLP(id: string) {
  const qc = useQueryClient()
  return useMutation({ mutationFn: () => lpApi.publish(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['lps', id] }) })
}

export function useEnrollments() {
  return useQuery<Enrollment[]>({ queryKey: ['enrollments'], queryFn: enrollmentsApi.list })
}

export function useEnrollment(id: string) {
  return useQuery<Enrollment>({ queryKey: ['enrollments', id], queryFn: () => enrollmentsApi.get(id), enabled: !!id })
}

export function useEnrollmentProgress(id: string) {
  return useQuery<ContentProgress[]>({ queryKey: ['enrollments', id, 'progress'], queryFn: () => enrollmentsApi.getProgress(id), enabled: !!id })
}

export function useMarkContentCompleted(enrollmentId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ contentId }: { contentId: string }) =>
      enrollmentsApi.updateProgress(enrollmentId, contentId, { status: 'COMPLETED', progress_percent: 100 }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['enrollments', enrollmentId] }),
  })
}

export function useGenerateQuiz(courseId: string) {
  return useMutation<GenerationJob, Error>({
    mutationFn: () => quizzesApi.generate(courseId),
  })
}

export function useGenerationJob(jobId: string | null) {
  return useQuery<GenerationJob>({
    queryKey: ['quiz-jobs', jobId],
    queryFn: () => quizzesApi.getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'PENDING' || status === 'PROCESSING' ? 3000 : false
    },
  })
}

export function useCourseQuiz(courseId: string) {
  return useQuery<Quiz>({
    queryKey: ['quiz', courseId],
    queryFn: () => quizzesApi.getForCourse(courseId),
    enabled: !!courseId,
    retry: false,
  })
}
