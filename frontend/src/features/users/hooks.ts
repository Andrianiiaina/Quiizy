import { useQuery } from '@tanstack/react-query'
import { usersApi } from './api'

export function useUsers(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
    enabled: options?.enabled ?? true,
  })
}

export function useUser(id: string) {
  return useQuery({
    queryKey: ['users', id],
    queryFn: () => usersApi.get(id),
    enabled: !!id,
  })
}
