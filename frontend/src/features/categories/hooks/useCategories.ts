import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { categoriesApi } from '../api'

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.list,
    staleTime: 1000 * 60 * 5,
  })
}

export function useCreateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['categories'] }),
  })
}
