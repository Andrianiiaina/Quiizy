import { useLocation, useNavigate, type Location } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../hooks/useAuth'

const schema = z.object({
  email: z.string().email('Adresse email invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
})
type FormData = z.infer<typeof schema>

export function LoginForm() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isLoginPending } = useAuth()
  const from = (location.state as { from?: Location })?.from?.pathname ?? '/'

  const { register, handleSubmit, setError, formState: { errors } } =
    useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    try {
      await login(data)
      navigate(from, { replace: true })
    } catch {
      setError('root', { message: 'Email ou mot de passe incorrect.' })
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email" type="email" autoComplete="email"
          {...register('email')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Mot de passe
        </label>
        <input
          id="password" type="password" autoComplete="current-password"
          {...register('password')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
      </div>

      {errors.root && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errors.root.message}</p>
      )}

      <button
        type="submit" disabled={isLoginPending}
        className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {isLoginPending ? 'Connexion…' : 'Se connecter'}
      </button>
    </form>
  )
}
