import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '@/components/common/ProtectedRoute'
import { AdminRoute } from '@/components/common/AdminRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { RegisterPage } from '@/features/auth/pages/RegisterPage'

function Dashboard() {
  return (
    <div className="rounded-lg border bg-white p-8 text-center">
      <h2 className="text-2xl font-bold text-gray-900">Tableau de bord</h2>
      <p className="mt-2 text-gray-500">Phase 2 — Authentification opérationnelle ✓</p>
    </div>
  )
}

export const router = createBrowserRouter([
  { path: '/login',    element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },

  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true,        element: <Navigate to="/dashboard" replace /> },
          { path: '/dashboard', element: <Dashboard /> },
        ],
      },
    ],
  },

  { path: '*', element: <Navigate to="/" replace /> },
])
