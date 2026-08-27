import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { assignmentsApi } from './api'
import type { Assignment } from '@/types/lms'

export function useAssignments() {
  return useQuery<Assignment[]>({
    queryKey: ['assignments'],
    queryFn: assignmentsApi.list,
  })
}

export function useCreateAssignment() {
  const qc = useQueryClient()
  return useMutation<Assignment, Error, Parameters<typeof assignmentsApi.create>[0]>({
    mutationFn: assignmentsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assignments'] }),
  })
}

export function useCancelAssignment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: assignmentsApi.cancel,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assignments'] }),
  })
}
