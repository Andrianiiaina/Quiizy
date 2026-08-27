import { createBrowserRouter, Navigate } from 'react-router-dom'
import { ProtectedRoute } from '@/components/common/ProtectedRoute'
import { AdminRoute } from '@/components/common/AdminRoute'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { RegisterPage } from '@/features/auth/pages/RegisterPage'
import { CoursesListPage } from '@/features/courses/pages/CoursesListPage'
import { CreateCoursePage } from '@/features/courses/pages/CreateCoursePage'
import { CourseDetailPage } from '@/features/courses/pages/CourseDetailPage'
import { CourseEditPage } from '@/features/courses/pages/CourseEditPage'
import { LearningPathsListPage } from '@/features/learning-paths/pages/LearningPathsListPage'
import { CreateLearningPathPage } from '@/features/learning-paths/pages/CreateLearningPathPage'
import { LearningPathDetailPage } from '@/features/learning-paths/pages/LearningPathDetailPage'
import { MyEnrollmentsPage } from '@/features/enrollments/pages/MyEnrollmentsPage'
import { EnrollmentDetailPage } from '@/features/enrollments/pages/EnrollmentDetailPage'
import { AssignmentsPage } from '@/features/assignments/pages/AssignmentsPage'
import { QuizAttemptPage } from '@/features/quizzes/pages/QuizAttemptPage'

export const router = createBrowserRouter([
  { path: '/login',    element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },

  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true,               element: <Navigate to="/courses" replace /> },
          { path: '/courses',          element: <CoursesListPage /> },
          { path: '/courses/new',      element: <CreateCoursePage /> },
          { path: '/courses/:id',      element: <CourseDetailPage /> },
          { path: '/courses/:id/edit', element: <CourseEditPage /> },
          { path: '/learning-paths',          element: <LearningPathsListPage /> },
          { path: '/learning-paths/new',      element: <CreateLearningPathPage /> },
          { path: '/learning-paths/:id',      element: <LearningPathDetailPage /> },
          { path: '/my-enrollments',          element: <MyEnrollmentsPage /> },
          { path: '/enrollments/:id',         element: <EnrollmentDetailPage /> },
          { path: '/quizzes/:quizId/attempt', element: <QuizAttemptPage /> },
          {
            element: <AdminRoute />,
            children: [
              { path: '/admin/assignments', element: <AssignmentsPage /> },
            ],
          },
        ],
      },
    ],
  },

  { path: '*', element: <Navigate to="/" replace /> },
])
