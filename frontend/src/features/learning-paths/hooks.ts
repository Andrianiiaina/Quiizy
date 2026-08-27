import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { lpApi } from './api'
import type { LearningPath } from '@/types/lms'

export function useLPs() {
  return useQuery<{ items: LearningPath[]; total: number; page: number; per_page: number }>({
    queryKey: ['lps'],
    queryFn: () => lpApi.list(),
  })
}

export function useLP(id: string) {
  return useQuery<LearningPath>({
    queryKey: ['lps', id],
    queryFn: () => lpApi.get(id),
    enabled: !!id,
  })
}

export function useLPCourses(id: string) {
  return useQuery({
    queryKey: ['lps', id, 'courses'],
    queryFn: () => lpApi.getCourses(id),
    enabled: !!id,
  })
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
  return useMutation({
    mutationFn: (data: Parameters<typeof lpApi.update>[1]) => lpApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['lps'] }),
  })
}

export function useDeleteLP(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => lpApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['lps'] }),
  })
}

export function usePublishLP(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => lpApi.publish(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['lps', id] }),
  })
}
