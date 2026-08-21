import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useCreateLP } from '@/features/lms/hooks'

const schema = z.object({
  title: z.string().min(1, 'Titre requis').max(255),
  description: z.string().optional(),
})
type FormData = z.infer<typeof schema>

export function CreateLearningPathPage() {
  const navigate = useNavigate()
  const { mutateAsync, isPending } = useCreateLP()
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    const lp = await mutateAsync({ title: data.title, description: data.description })
    navigate(`/learning-paths/${(lp as { id: string }).id}`, { replace: true })
  }

  const inputCls = 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Créer un parcours</h1>
      <div className="rounded-xl border bg-white p-8 shadow-sm">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Titre *</label>
            <input type="text" {...register('title')} className={inputCls} />
            {errors.title && <p className="mt-1 text-xs text-red-600">{errors.title.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea rows={3} {...register('description')} className={inputCls + ' resize-none'} />
          </div>
          <button type="submit" disabled={isPending} className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
            {isPending ? 'Création…' : 'Créer'}
          </button>
        </form>
      </div>
    </div>
  )
}
