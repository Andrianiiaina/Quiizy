import { useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi, type LoginRequest, type RegisterRequest } from '../api'
import { useAuthContext } from '@/lib/auth'

export function useAuth() {
  const context = useAuthContext()
  const queryClient = useQueryClient()

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (user) => {
      queryClient.setQueryData(['auth', 'me'], user)
    },
  })

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.setQueryData(['auth', 'me'], null)
      queryClient.removeQueries({ queryKey: ['auth'] })
    },
  })

  const registerMutation = useMutation({
    mutationFn: authApi.register,
  })

  return {
    ...context,
    login: (data: LoginRequest) => loginMutation.mutateAsync(data),
    logout: () => logoutMutation.mutateAsync(),
    register: (data: RegisterRequest) => registerMutation.mutateAsync(data),
    isLoginPending: loginMutation.isPending,
    isLogoutPending: logoutMutation.isPending,
    isRegisterPending: registerMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  }
}
