import { useNavigate, useParams } from 'react-router-dom'
import { CourseForm, type CourseFormData } from '../components/CourseForm'
import { useCourse, useUpdateCourse } from '../hooks/useCourses'

export function CourseEditPage() {
  const { id = '' } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: course, isLoading } = useCourse(id)
  const { mutateAsync, isPending } = useUpdateCourse(id)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  if (!course) return <p className="text-gray-500">Cours introuvable.</p>

  const handleSubmit = async (data: CourseFormData) => {
    await mutateAsync({
      title: data.title,
      description: data.description || null,
      category_id: data.category_id || null,
    })
    navigate(`/courses/${id}`, { replace: true })
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Modifier le cours</h1>
      <div className="rounded-xl border bg-white p-8 shadow-sm">
        <CourseForm
          defaultValues={{
            title: course.title,
            description: course.description ?? '',
            category_id: course.category_id,
          }}
          onSubmit={handleSubmit}
          isPending={isPending}
          submitLabel="Enregistrer"
        />
      </div>
    </div>
  )
}
