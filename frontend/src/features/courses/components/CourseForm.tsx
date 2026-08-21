import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCategories } from '@/features/categories/hooks/useCategories'

const schema = z.object({
  title: z.string().min(1, 'Titre requis').max(255),
  description: z.string().max(5000).optional().or(z.literal('')),
  category_id: z.string().uuid().optional().nullable(),
})

export type CourseFormData = z.infer<typeof schema>

interface CourseFormProps {
  defaultValues?: Partial<CourseFormData>
  onSubmit: (data: CourseFormData) => Promise<void>
  isPending: boolean
  submitLabel: string
}

const inputCls = 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'

export function CourseForm({ defaultValues, onSubmit, isPending, submitLabel }: CourseFormProps) {
  const { data: categories = [] } = useCategories()

  const { register, handleSubmit, setError, formState: { errors } } =
    useForm<CourseFormData>({
      resolver: zodResolver(schema),
      defaultValues,
    })

  const handleFormSubmit = async (data: CourseFormData) => {
    try {
      await onSubmit(data)
    } catch {
      setError('root', { message: 'Une erreur est survenue. Réessayez.' })
    }
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700">
          Titre <span className="text-red-500">*</span>
        </label>
        <input id="title" type="text" {...register('title')} className={inputCls} />
        {errors.title && <p className="mt-1 text-xs text-red-600">{errors.title.message}</p>}
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          id="description"
          rows={4}
          {...register('description')}
          className={inputCls + ' resize-none'}
        />
        {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>}
      </div>

      <div>
        <label htmlFor="category_id" className="block text-sm font-medium text-gray-700">
          Catégorie
        </label>
        <select id="category_id" {...register('category_id')} className={inputCls}>
          <option value="">Sans catégorie</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>
      </div>

      {errors.root && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errors.root.message}</p>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {isPending ? 'Enregistrement…' : submitLabel}
      </button>
    </form>
  )
}
