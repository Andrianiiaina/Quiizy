import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { coursesApi } from '../api'
import type { CreateCourseRequest, UpdateCourseRequest } from '@/types/course'

export function useCourses(params?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: ['courses', params],
    queryFn: () => coursesApi.list(params),
  })
}

export function useCourse(id: string) {
  return useQuery({
    queryKey: ['courses', id],
    queryFn: () => coursesApi.get(id),
    enabled: !!id,
  })
}

export function useCreateCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateCourseRequest) => coursesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}

export function useUpdateCourse(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: UpdateCourseRequest) => coursesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['courses', id] })
      qc.invalidateQueries({ queryKey: ['courses'] })
    },
  })
}

export function useDeleteCourse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => coursesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })
}

export function usePublishCourse(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => coursesApi.publish(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses', id] }),
  })
}

export function useArchiveCourse(id: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => coursesApi.archive(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses', id] }),
  })
}
