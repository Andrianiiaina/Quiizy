import type { CourseStatus } from '@/types/course'

const LABELS: Record<CourseStatus, string> = {
  DRAFT: 'Brouillon',
  PUBLISHED: 'Publié',
  ARCHIVED: 'Archivé',
}

const STYLES: Record<CourseStatus, string> = {
  DRAFT: 'bg-gray-100 text-gray-700',
  PUBLISHED: 'bg-green-100 text-green-700',
  ARCHIVED: 'bg-yellow-100 text-yellow-700',
}

export function CourseStatusBadge({ status }: { status: CourseStatus }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[status]}`}>
      {LABELS[status]}
    </span>
  )
}
