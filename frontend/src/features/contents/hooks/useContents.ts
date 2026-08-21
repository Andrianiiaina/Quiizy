import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { contentsApi, filesApi } from '../api'
import type { CreateContentRequest } from '@/types/content'

export function useCourseContents(courseId: string) {
  return useQuery({
    queryKey: ['contents', courseId],
    queryFn: () => contentsApi.listForCourse(courseId),
    enabled: !!courseId,
  })
}

export function useCreateContent(courseId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateContentRequest) => contentsApi.create(courseId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contents', courseId] }),
  })
}

export function useDeleteContent(courseId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => contentsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contents', courseId] }),
  })
}

export function useReorderContents(courseId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (items: { id: string; position: number }[]) => contentsApi.reorder(courseId, items),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['contents', courseId] }),
  })
}

export function useUploadFile() {
  return useMutation({ mutationFn: filesApi.upload })
}
