import { Link } from 'react-router-dom'
import { useEnrollments } from '@/features/lms/hooks'

const STATUS_LABELS: Record<string, string> = {
  NOT_STARTED: 'Non démarré',
  IN_PROGRESS: 'En cours',
  COMPLETED: 'Terminé',
  OVERDUE: 'En retard',
  CANCELLED: 'Annulé',
}
const STATUS_STYLE: Record<string, string> = {
  NOT_STARTED: 'bg-gray-100 text-gray-700',
  IN_PROGRESS: 'bg-blue-100 text-blue-700',
  COMPLETED: 'bg-green-100 text-green-700',
  OVERDUE: 'bg-red-100 text-red-700',
  CANCELLED: 'bg-gray-100 text-gray-400',
}

export function MyEnrollmentsPage() {
  const { data: enrollments = [] as import('@/types/lms').Enrollment[], isLoading } = useEnrollments()

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Mes inscriptions</h1>
      {isLoading && <div className="flex justify-center py-12"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" /></div>}
      {!isLoading && enrollments.length === 0 && (
        <p className="text-gray-500">Aucune inscription pour le moment. Un administrateur doit vous affecter un cours.</p>
      )}
      <div className="space-y-3">
        {enrollments.map(e => (
          <div key={e.id} className="flex items-center justify-between rounded-lg border bg-white px-4 py-3 shadow-sm">
            <div>
              <Link to={`/courses/${e.course_id}`} className="font-medium text-gray-900 hover:text-blue-600">
                Cours {e.course_id.slice(0, 8)}…
              </Link>
              {e.due_date && <p className="text-xs text-gray-500">Échéance : {new Date(e.due_date).toLocaleDateString('fr-FR')}</p>}
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{e.progress_percent}%</p>
                <div className="mt-1 h-1.5 w-24 rounded-full bg-gray-200">
                  <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${e.progress_percent}%` }} />
                </div>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[e.status]}`}>
                {STATUS_LABELS[e.status]}
              </span>
              <Link to={`/enrollments/${e.id}`} className="text-sm text-blue-600 hover:underline">Détail</Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
