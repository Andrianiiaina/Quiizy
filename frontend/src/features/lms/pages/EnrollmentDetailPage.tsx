import { Link, useParams } from 'react-router-dom'
import { useEnrollment, useEnrollmentProgress, useMarkContentCompleted, useCourseQuiz } from '@/features/lms/hooks'
import { useCourse } from '@/features/courses/hooks/useCourses'
import { useCourseContents } from '@/features/contents/hooks/useContents'
import type { ContentProgress } from '@/types/lms'

export function EnrollmentDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const { data: enrollment, isLoading } = useEnrollment(id)
  const { data: course } = useCourse(enrollment?.course_id ?? '')
  const { data: contents = [] } = useCourseContents(enrollment?.course_id ?? '')
  const { data: progressList = [] } = useEnrollmentProgress(id)
  const { data: quiz } = useCourseQuiz(enrollment?.course_id ?? '')
  const { mutateAsync: markCompleted } = useMarkContentCompleted(id)

  if (isLoading) return <div className="flex justify-center py-12"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" /></div>
  if (!enrollment) return <p className="text-gray-500">Inscription introuvable.</p>

  const progressMap: Record<string, ContentProgress> = {}
  progressList.forEach((p: ContentProgress) => { progressMap[p.content_id] = p })

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{course?.title ?? 'Cours'}</h1>
        <div className="mt-2 flex items-center gap-4">
          <div className="flex-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Progression</span>
              <span className="font-medium">{enrollment.progress_percent}%</span>
            </div>
            <div className="mt-1 h-2 rounded-full bg-gray-200">
              <div className="h-2 rounded-full bg-blue-500 transition-all" style={{ width: `${enrollment.progress_percent}%` }} />
            </div>
          </div>
          {quiz && enrollment.status !== 'CANCELLED' && (
            <Link
              to={`/quizzes/${quiz.id}/attempt?enrollment_id=${id}`}
              className="rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-700"
            >
              Passer le quiz
            </Link>
          )}
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Contenus</h2>
        <div className="space-y-2">
          {contents.map(content => {
            const cp = progressMap[content.id]
            const isCompleted = cp?.status === 'COMPLETED'
            return (
              <div key={content.id} className="flex items-center justify-between rounded-lg border bg-white px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-900">{content.title}</p>
                  <p className="text-xs text-gray-500">{content.type}</p>
                </div>
                <div className="flex items-center gap-2">
                  {isCompleted ? (
                    <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-700">✓ Terminé</span>
                  ) : (
                    <button
                      onClick={() => markCompleted({ contentId: content.id })}
                      className="rounded-md border px-3 py-1 text-xs hover:bg-gray-50"
                    >
                      Marquer terminé
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
