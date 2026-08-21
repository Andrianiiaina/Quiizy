import { Link, useNavigate, useParams } from 'react-router-dom'
import { useCourse, useDeleteCourse, usePublishCourse, useArchiveCourse } from '../hooks/useCourses'
import { CourseStatusBadge } from '../components/CourseStatusBadge'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { useCourseContents, useDeleteContent, useReorderContents } from '@/features/contents/hooks/useContents'
import { ContentCard } from '@/features/contents/components/ContentCard'
import { AddContentForm } from '@/features/contents/components/AddContentForm'
import type { CourseContent } from '@/types/content'

export function CourseDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: course, isLoading } = useCourse(id)
  const { data: contents = [] } = useCourseContents(id)
  const { user } = useAuth()
  const { mutateAsync: deleteCourse, isPending: isDeleting } = useDeleteCourse()
  const { mutateAsync: publishCourse, isPending: isPublishing } = usePublishCourse(id)
  const { mutateAsync: archiveCourse, isPending: isArchiving } = useArchiveCourse(id)
  const { mutateAsync: deleteContent } = useDeleteContent(id)
  const { mutateAsync: reorder } = useReorderContents(id)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  if (!course) return <p className="text-gray-500">Cours introuvable.</p>

  const canEdit = user?.id === course.owner_id || user?.role === 'ADMIN'

  const handleDelete = async () => {
    if (!confirm('Supprimer ce cours ?')) return
    await deleteCourse(id)
    navigate('/courses', { replace: true })
  }

  const handleMoveUp = async (content: CourseContent, index: number) => {
    if (index === 0) return
    const swapped = [...contents]
    const updated = swapped.map((c, i) => {
      if (i === index) return { id: c.id, position: contents[index - 1].position }
      if (i === index - 1) return { id: c.id, position: contents[index].position }
      return { id: c.id, position: c.position }
    })
    await reorder(updated)
  }

  const handleMoveDown = async (content: CourseContent, index: number) => {
    if (index === contents.length - 1) return
    const updated = contents.map((c, i) => {
      if (i === index) return { id: c.id, position: contents[index + 1].position }
      if (i === index + 1) return { id: c.id, position: contents[index].position }
      return { id: c.id, position: c.position }
    })
    await reorder(updated)
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{course.title}</h1>
            <CourseStatusBadge status={course.status} />
          </div>
          {course.category && <p className="mt-1 text-sm text-blue-600">{course.category.name}</p>}
        </div>

        {canEdit && (
          <div className="flex shrink-0 gap-2">
            {course.status === 'DRAFT' && (
              <button onClick={() => publishCourse()} disabled={isPublishing}
                className="rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50">
                Publier
              </button>
            )}
            {course.status === 'PUBLISHED' && (
              <button onClick={() => archiveCourse()} disabled={isArchiving}
                className="rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50">
                Archiver
              </button>
            )}
            <Link to={`/courses/${id}/edit`}
              className="rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-gray-50">
              Modifier
            </Link>
            <button onClick={handleDelete} disabled={isDeleting}
              className="rounded-md border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50">
              Supprimer
            </button>
          </div>
        )}
      </div>

      {/* Description */}
      {course.description && (
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <p className="whitespace-pre-wrap text-gray-700">{course.description}</p>
        </div>
      )}

      {/* Contents */}
      <div>
        <h2 className="mb-3 text-lg font-semibold text-gray-900">
          Contenus {contents.length > 0 && <span className="text-sm font-normal text-gray-500">({contents.length})</span>}
        </h2>

        {contents.length === 0 && !canEdit && (
          <p className="text-sm text-gray-500">Aucun contenu pour le moment.</p>
        )}

        <div className="space-y-2">
          {contents.map((c, i) => (
            <ContentCard
              key={c.id} content={c} canEdit={canEdit}
              isFirst={i === 0} isLast={i === contents.length - 1}
              onMoveUp={() => handleMoveUp(c, i)}
              onMoveDown={() => handleMoveDown(c, i)}
              onDelete={() => deleteContent(c.id)}
            />
          ))}
        </div>

        {canEdit && (
          <div className="mt-4">
            <AddContentForm courseId={id} onSuccess={() => {}} />
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400">
        Modifié le {new Date(course.updated_at).toLocaleDateString('fr-FR')}
      </p>
    </div>
  )
}
