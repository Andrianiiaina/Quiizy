import { Link } from 'react-router-dom'
import { useLPs } from '@/features/lms/hooks'
import type { LearningPath } from '@/types/lms'

const STATUS_STYLE: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700',
  PUBLISHED: 'bg-green-100 text-green-700',
  ARCHIVED: 'bg-yellow-100 text-yellow-700',
}

function LPCard({ lp }: { lp: LearningPath }) {
  return (
    <div className="flex flex-col rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <h3 className="font-semibold text-gray-900">{lp.title}</h3>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[lp.status]}`}>{lp.status}</span>
      </div>
      {lp.description && <p className="mt-1 text-sm text-gray-500 line-clamp-2">{lp.description}</p>}
      <div className="mt-4 flex justify-end">
        <Link to={`/learning-paths/${lp.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-500">Voir →</Link>
      </div>
    </div>
  )
}

export function LearningPathsListPage() {
  const { data, isLoading } = useLPs()
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Parcours</h1>
        <Link to="/learning-paths/new" className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">+ Créer</Link>
      </div>
      {isLoading ? <div className="flex justify-center py-12"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" /></div> : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.items.map(lp => <LPCard key={lp.id} lp={lp} />)}
        </div>
      )}
    </div>
  )
}
