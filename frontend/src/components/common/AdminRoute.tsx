import { Navigate, Outlet } from 'react-router-dom'
import { useAuthContext } from '@/lib/auth'

function Spinner() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
    </div>
  )
}

export function AdminRoute() {
  const { user, isLoading } = useAuthContext()

  if (isLoading) return <Spinner />
  if (!user || user.role !== 'ADMIN') return <Navigate to="/" replace />
  return <Outlet />
}
