import { createBrowserRouter } from 'react-router-dom'

function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gray-50">
      <h1 className="text-5xl font-bold tracking-tight text-gray-900">LMS</h1>
      <p className="text-lg text-gray-500">Plateforme e-learning multi-utilisateur</p>
      <span className="rounded-full bg-blue-100 px-4 py-1 text-sm font-medium text-blue-700">
        Phase 1 — Skeleton
      </span>
    </div>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
])
