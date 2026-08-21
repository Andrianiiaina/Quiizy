import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthContext } from '@/lib/auth'

function Spinner() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
    </div>
  )
}

export function ProtectedRoute() {
  const { user, isLoading } = useAuthContext()
  const location = useLocation()

  if (isLoading) return <Spinner />
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}
