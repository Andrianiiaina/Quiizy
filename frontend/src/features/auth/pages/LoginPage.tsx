import { Link } from 'react-router-dom'
import { LoginForm } from '../components/LoginForm'

export function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">LMS</h1>
          <p className="mt-2 text-sm text-gray-500">Connectez-vous à votre compte</p>
        </div>
        <div className="rounded-xl border bg-white p-8 shadow-sm">
          <LoginForm />
          <p className="mt-4 text-center text-sm text-gray-500">
            Pas encore de compte ?{' '}
            <Link to="/register" className="font-medium text-blue-600 hover:text-blue-500">
              Créer un compte
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
