export type UserRole = 'ADMIN' | 'USER'

export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}
