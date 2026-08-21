import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../hooks/useAuth'
import type { ApiError } from '@/types/api'
import type { AxiosError } from 'axios'

const schema = z
  .object({
    email: z.string().email('Adresse email invalide'),
    first_name: z.string().min(1, 'Prénom requis').max(100),
    last_name: z.string().min(1, 'Nom requis').max(100),
    password: z.string().min(8, '8 caractères minimum'),
    confirm_password: z.string(),
  })
  .refine((d) => d.password === d.confirm_password, {
    message: 'Les mots de passe ne correspondent pas.',
    path: ['confirm_password'],
  })
type FormData = z.infer<typeof schema>

export function RegisterForm() {
  const navigate = useNavigate()
  const { register: registerUser, isRegisterPending } = useAuth()

  const { register, handleSubmit, setError, formState: { errors } } =
    useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async ({ confirm_password: _, ...data }: FormData) => {
    try {
      await registerUser(data)
      navigate('/login', { replace: true })
    } catch (err) {
      const code = (err as AxiosError<ApiError>)?.response?.data?.code
      if (code === 'EMAIL_ALREADY_EXISTS') {
        setError('email', { message: 'Cet email est déjà utilisé.' })
      } else {
        setError('root', { message: 'Une erreur est survenue. Réessayez.' })
      }
    }
  }

  const inputCls = 'mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">Prénom</label>
          <input id="first_name" type="text" autoComplete="given-name" {...register('first_name')} className={inputCls} />
          {errors.first_name && <p className="mt-1 text-xs text-red-600">{errors.first_name.message}</p>}
        </div>
        <div>
          <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">Nom</label>
          <input id="last_name" type="text" autoComplete="family-name" {...register('last_name')} className={inputCls} />
          {errors.last_name && <p className="mt-1 text-xs text-red-600">{errors.last_name.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="reg-email" className="block text-sm font-medium text-gray-700">Email</label>
        <input id="reg-email" type="email" autoComplete="email" {...register('email')} className={inputCls} />
        {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
      </div>

      <div>
        <label htmlFor="reg-password" className="block text-sm font-medium text-gray-700">Mot de passe</label>
        <input id="reg-password" type="password" autoComplete="new-password" {...register('password')} className={inputCls} />
        {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
      </div>

      <div>
        <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">Confirmer</label>
        <input id="confirm_password" type="password" autoComplete="new-password" {...register('confirm_password')} className={inputCls} />
        {errors.confirm_password && <p className="mt-1 text-xs text-red-600">{errors.confirm_password.message}</p>}
      </div>

      {errors.root && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errors.root.message}</p>
      )}

      <button
        type="submit" disabled={isRegisterPending}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {isRegisterPending ? 'Création…' : 'Créer un compte'}
      </button>
    </form>
  )
}
