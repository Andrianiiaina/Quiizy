import { Link } from 'react-router-dom'
import { useCourses } from '../hooks/useCourses'
import { CourseCard } from '../components/CourseCard'

export function CoursesListPage() {
  const { data, isLoading } = useCourses()

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Cours</h1>
        <Link
          to="/courses/new"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
        >
          + Créer un cours
        </Link>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      )}

      {!isLoading && data?.items.length === 0 && (
        <div className="rounded-lg border-2 border-dashed border-gray-200 p-12 text-center">
          <p className="text-gray-500">Aucun cours pour le moment.</p>
          <Link to="/courses/new" className="mt-2 inline-block text-sm text-blue-600 hover:underline">
            Créer votre premier cours
          </Link>
        </div>
      )}

      {!isLoading && data && data.items.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  )
}
