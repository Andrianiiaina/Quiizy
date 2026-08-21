import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { AuthContext } from '@/lib/auth'
import { authApi } from '@/features/auth/api'
import type { User } from '@/types/auth'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 1000 * 60, retry: 1 } },
})

function AuthProvider({ children }: { children: ReactNode }) {
  const { data: user, isLoading } = useQuery<User | null>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      try { return await authApi.me() } catch { return null }
    },
    staleTime: Infinity,
    retry: false,
  })

  return (
    <AuthContext.Provider value={{ user: user ?? null, isLoading, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}
