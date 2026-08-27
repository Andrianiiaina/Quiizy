import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { enrollmentsApi } from './api'
import type { ContentProgress, Enrollment } from '@/types/lms'

export function useEnrollments() {
  return useQuery<Enrollment[]>({
    queryKey: ['enrollments'],
    queryFn: enrollmentsApi.list,
  })
}

export function useEnrollment(id: string) {
  return useQuery<Enrollment>({
    queryKey: ['enrollments', id],
    queryFn: () => enrollmentsApi.get(id),
    enabled: !!id,
  })
}

export function useEnrollmentProgress(id: string) {
  return useQuery<ContentProgress[]>({
    queryKey: ['enrollments', id, 'progress'],
    queryFn: () => enrollmentsApi.getProgress(id),
    enabled: !!id,
  })
}

export function useMarkContentCompleted(enrollmentId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ contentId }: { contentId: string }) =>
      enrollmentsApi.updateProgress(enrollmentId, contentId, { status: 'COMPLETED', progress_percent: 100 }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['enrollments', enrollmentId] }),
  })
}
