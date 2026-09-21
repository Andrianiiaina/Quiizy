import { useUsers } from '@/features/users/hooks'

const ROLE_STYLE: Record<string, string> = {
  ADMIN: 'bg-purple-100 text-purple-700',
  USER: 'bg-gray-100 text-gray-700',
}

export function UsersListPage() {
  const { data: users = [], isLoading } = useUsers()

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Utilisateurs</h1>
      {isLoading ? (
        <div className="flex justify-center py-12"><div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" /></div>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-500">Nom</th>
                <th className="px-4 py-2 text-left font-medium text-gray-500">Email</th>
                <th className="px-4 py-2 text-left font-medium text-gray-500">Rôle</th>
                <th className="px-4 py-2 text-left font-medium text-gray-500">Statut</th>
                <th className="px-4 py-2 text-left font-medium text-gray-500">Créé le</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {users.map((u) => (
                <tr key={u.id}>
                  <td className="px-4 py-2 text-gray-900">{u.first_name} {u.last_name}</td>
                  <td className="px-4 py-2 text-gray-600">{u.email}</td>
                  <td className="px-4 py-2">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${ROLE_STYLE[u.role]}`}>{u.role}</span>
                  </td>
                  <td className="px-4 py-2">
                    {u.is_active ? (
                      <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">Actif</span>
                    ) : (
                      <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700">Inactif</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-gray-500">{new Date(u.created_at).toLocaleDateString('fr-FR')}</td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-400">Aucun utilisateur.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
