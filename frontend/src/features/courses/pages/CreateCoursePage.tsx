import { useNavigate } from 'react-router-dom'
import { CourseForm, type CourseFormData } from '../components/CourseForm'
import { useCreateCourse } from '../hooks/useCourses'

export function CreateCoursePage() {
  const navigate = useNavigate()
  const { mutateAsync, isPending } = useCreateCourse()

  const handleSubmit = async (data: CourseFormData) => {
    const course = await mutateAsync({
      title: data.title,
      description: data.description || null,
      category_id: data.category_id || null,
    })
    navigate(`/courses/${course.id}`, { replace: true })
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Créer un cours</h1>
      <div className="rounded-xl border bg-white p-8 shadow-sm">
        <CourseForm onSubmit={handleSubmit} isPending={isPending} submitLabel="Créer le cours" />
      </div>
    </div>
  )
}
