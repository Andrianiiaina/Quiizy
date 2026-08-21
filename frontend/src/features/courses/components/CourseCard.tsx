import { Link } from 'react-router-dom'
import type { Course } from '@/types/course'
import { CourseStatusBadge } from './CourseStatusBadge'

export function CourseCard({ course }: { course: Course }) {
  return (
    <div className="flex flex-col rounded-lg border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-gray-900 line-clamp-2">{course.title}</h3>
        <CourseStatusBadge status={course.status} />
      </div>
      {course.category && (
        <p className="mt-1 text-xs text-blue-600">{course.category.name}</p>
      )}
      {course.description && (
        <p className="mt-2 flex-1 text-sm text-gray-500 line-clamp-3">{course.description}</p>
      )}
      <div className="mt-4 flex justify-end">
        <Link
          to={`/courses/${course.id}`}
          className="text-sm font-medium text-blue-600 hover:text-blue-500"
        >
          Voir →
        </Link>
      </div>
    </div>
  )
}
