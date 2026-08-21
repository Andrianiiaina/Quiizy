import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '@/components/common/ProtectedRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { RegisterPage } from '@/features/auth/pages/RegisterPage'
import { CoursesListPage } from '@/features/courses/pages/CoursesListPage'
import { CreateCoursePage } from '@/features/courses/pages/CreateCoursePage'
import { CourseDetailPage } from '@/features/courses/pages/CourseDetailPage'
import { CourseEditPage } from '@/features/courses/pages/CourseEditPage'

function Dashboard() {
  return (
    <div className="rounded-lg border bg-white p-8 text-center">
      <h2 className="text-2xl font-bold text-gray-900">Tableau de bord</h2>
      <p className="mt-2 text-gray-500">Phase 3 — Cours opérationnels ✓</p>
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
          { index: true,               element: <Navigate to="/dashboard" replace /> },
          { path: '/dashboard',        element: <Dashboard /> },
          { path: '/courses',          element: <CoursesListPage /> },
          { path: '/courses/new',      element: <CreateCoursePage /> },
          { path: '/courses/:id',      element: <CourseDetailPage /> },
          { path: '/courses/:id/edit', element: <CourseEditPage /> },
        ],
      },
    ],
  },

  { path: '*', element: <Navigate to="/" replace /> },
])
