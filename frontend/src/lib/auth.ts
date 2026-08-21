import { createContext, useContext } from 'react'
import type { User } from '@/types/auth'

export interface AuthContextValue {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
}

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  isAuthenticated: false,
})

export function useAuthContext(): AuthContextValue {
  return useContext(AuthContext)
}
