import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useLP, useLPCourses, usePublishLP } from '@/features/lms/hooks'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { lpApi } from '@/features/lms/api'
import { useCourses } from '@/features/courses/hooks/useCourses'
import { useQueryClient, useMutation } from '@tanstack/react-query'
import type { LPCourseItem } from '@/types/lms'

export function LearningPathDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: lp, isLoading } = useLP(id)
  const { data: lpCourses = [] as LPCourseItem[] } = useLPCourses(id)
  const { data: allCourses } = useCourses()
  const { user } = useAuth()
  const qc = useQueryClient()
  const { mutateAsync: publishLP, isPending: isPublishing } = usePublishLP(id)
  const [addingCourseId, setAddingCourseId] = useState<string>('')

  const { mutateAsync: deleteLP } = useMutation({
    mutationFn: () => lpApi.delete(id),
    onSuccess: () => { navigate('/learning-paths', { replace: true }) },
  })

  if (isLoading) return <div className="flex justify-center py-12"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" /></div>
  if (!lp) return <p className="text-gray-500">Parcours introuvable.</p>

  const canEdit = user?.id === lp.created_by || user?.role === 'ADMIN'
  const lpCourseIds = new Set(lpCourses.map((c: LPCourseItem) => c.course_id))
  const availableCourses = allCourses?.items.filter((c: { id: string }) => !lpCourseIds.has(c.id)) ?? []

  const handleAddCourse = async () => {
    if (!addingCourseId) return
    await lpApi.addCourse(id, addingCourseId)
    qc.invalidateQueries({ queryKey: ['lps', id, 'courses'] })
    setAddingCourseId('')
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{lp.title}</h1>
          {lp.description && <p className="mt-1 text-gray-500">{lp.description}</p>}
        </div>
        {canEdit && (
          <div className="flex gap-2">
            {lp.status === 'DRAFT' && (
              <button onClick={() => publishLP()} disabled={isPublishing} className="rounded-md bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50">Publier</button>
            )}
            <button onClick={() => { if (confirm('Supprimer ?')) deleteLP() }} className="rounded-md border border-red-200 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50">Supprimer</button>
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Cours du parcours ({lpCourses.length})</h2>
        {lpCourses.length === 0 && <p className="text-sm text-gray-500">Aucun cours ajouté.</p>}
        <div className="space-y-2">
          {lpCourses.map((lpc: LPCourseItem, i: number) => (
            <div key={lpc.course_id} className="flex items-center justify-between rounded-lg border bg-white px-4 py-2">
              <span className="text-sm text-gray-700">
                #{i + 1} — <Link to={`/courses/${lpc.course_id}`} className="text-blue-600 hover:underline">{lpc.course_id.slice(0, 8)}…</Link>
              </span>
              {canEdit && (
                <button onClick={() => { lpApi.removeCourse(id, lpc.course_id).then(() => qc.invalidateQueries({ queryKey: ['lps', id, 'courses'] })) }} className="text-xs text-red-500 hover:underline">Retirer</button>
              )}
            </div>
          ))}
        </div>
        {canEdit && (
          <div className="mt-4 flex gap-2">
            <select value={addingCourseId} onChange={e => setAddingCourseId(e.target.value)} className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm">
              <option value="">Ajouter un cours…</option>
              {availableCourses.map((c: { id: string; title: string }) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
            <button onClick={handleAddCourse} disabled={!addingCourseId} className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50">Ajouter</button>
          </div>
        )}
      </div>
    </div>
  )
}
