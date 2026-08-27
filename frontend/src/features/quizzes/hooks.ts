import { useMutation, useQuery } from '@tanstack/react-query'
import { quizzesApi } from './api'
import type { GenerationJob, Quiz } from '@/types/lms'

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
