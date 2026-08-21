import { useNavigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'

export function AppLayout() {
  const navigate = useNavigate()
  const { user, logout, isLogoutPending } = useAuth()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <span className="text-xl font-bold text-gray-900">LMS</span>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.first_name} {user?.last_name}
              {user?.role === 'ADMIN' && (
                <span className="ml-2 rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700">
                  Admin
                </span>
              )}
            </span>
            <button
              onClick={handleLogout}
              disabled={isLogoutPending}
              className="rounded-md border px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              Déconnexion
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
