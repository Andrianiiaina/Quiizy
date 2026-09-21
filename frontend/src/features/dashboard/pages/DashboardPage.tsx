import { Link } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useCourses } from '@/features/courses/hooks/useCourses'
import { useEnrollments } from '@/features/enrollments/hooks'
import { useAssignments } from '@/features/assignments/hooks'
import { useUsers } from '@/features/users/hooks'

function StatCard({ label, value, to }: { label: string; value: number | string; to?: string }) {
  const content = (
    <div className="rounded-xl border bg-white p-6 shadow-sm transition hover:shadow-md">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
    </div>
  )
  return to ? <Link to={to}>{content}</Link> : content
}

export function DashboardPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'ADMIN'

  const { data: courses } = useCourses({ per_page: 100 })
  const { data: enrollments = [] } = useEnrollments()
  const { data: assignments = [] } = useAssignments({ enabled: isAdmin })
  const { data: users = [] } = useUsers({ enabled: isAdmin })

  const myCourses = courses?.items.filter((c) => c.owner_id === user?.id) ?? []
  const inProgress = enrollments.filter((e) => e.status === 'IN_PROGRESS').length
  const completed = enrollments.filter((e) => e.status === 'COMPLETED').length

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Bonjour {user?.first_name} 👋
        </h1>
        <p className="mt-1 text-gray-500">Voici un aperçu de votre activité.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Mes cours" value={myCourses.length} to="/courses" />
        <StatCard label="Mes inscriptions" value={enrollments.length} to="/my-enrollments" />
        <StatCard label="En cours" value={inProgress} to="/my-enrollments" />
        <StatCard label="Terminées" value={completed} to="/my-enrollments" />
      </div>

      {isAdmin && (
        <div>
          <h2 className="mb-3 text-lg font-semibold text-gray-900">Administration</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatCard label="Utilisateurs" value={users.length} to="/admin/users" />
            <StatCard label="Affectations" value={assignments.length} to="/admin/assignments" />
            <StatCard label="Parcours" value="—" to="/learning-paths" />
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <Link to="/courses/new" className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
          + Créer un cours
        </Link>
        <Link to="/courses" className="rounded-md border px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
          Voir tous les cours
        </Link>
      </div>
    </div>
  )
}
