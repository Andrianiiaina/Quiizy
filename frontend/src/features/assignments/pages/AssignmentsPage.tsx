import { useState } from 'react'
import { useAssignments, useCreateAssignment, useCancelAssignment } from '@/features/assignments/hooks'
import { useLPs } from '@/features/learning-paths/hooks'
import { useCourses } from '@/features/courses/hooks/useCourses'

export function AssignmentsPage() {
  const { data: courses } = useCourses()
  const { data: lps } = useLPs()
  const { data: assignments = [], isLoading } = useAssignments()
  const { mutateAsync: createAssignment, isPending } = useCreateAssignment()
  const { mutateAsync: cancelAssignment } = useCancelAssignment()

  const [form, setForm] = useState({ user_id: '', target_type: 'COURSE', target_id: '', due_date: '' })
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await createAssignment({ ...form, due_date: form.due_date || undefined })
      setForm({ user_id: '', target_type: 'COURSE', target_id: '', due_date: '' })
    } catch (err: unknown) {
      setError((err as { response?: { data?: { message?: string } } })?.response?.data?.message ?? 'Erreur')
    }
  }

  const inputCls = 'block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Affectations</h1>

      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h2 className="mb-4 font-semibold">Nouvelle affectation</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">UUID de l'utilisateur *</label>
            <input type="text" value={form.user_id} onChange={e => setForm(p => ({ ...p, user_id: e.target.value }))} className={inputCls} placeholder="uuid" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
            <select value={form.target_type} onChange={e => setForm(p => ({ ...p, target_type: e.target.value, target_id: '' }))} className={inputCls}>
              <option value="COURSE">Cours</option>
              <option value="LEARNING_PATH">Parcours</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">{form.target_type === 'COURSE' ? 'Cours' : 'Parcours'} *</label>
            <select value={form.target_id} onChange={e => setForm(p => ({ ...p, target_id: e.target.value }))} className={inputCls}>
              <option value="">Sélectionner…</option>
              {form.target_type === 'COURSE'
                ? courses?.items.map(c => <option key={c.id} value={c.id}>{c.title}</option>)
                : lps?.items.map((lp: { id: string; title: string }) => <option key={lp.id} value={lp.id}>{lp.title}</option>)
              }
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Échéance</label>
            <input type="date" value={form.due_date} onChange={e => setForm(p => ({ ...p, due_date: e.target.value }))} className={inputCls} />
          </div>
          {error && <p className="col-span-2 text-sm text-red-600">{error}</p>}
          <div className="col-span-2">
            <button type="submit" disabled={isPending || !form.user_id || !form.target_id} className="rounded-md bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
              {isPending ? 'Création…' : 'Affecter'}
            </button>
          </div>
        </form>
      </div>

      <div>
        <h2 className="mb-3 font-semibold">Affectations existantes</h2>
        {isLoading ? <p className="text-gray-500">Chargement…</p> : (
          <div className="space-y-2">
            {assignments.map(a => (
              <div key={a.id} className="flex items-center justify-between rounded-lg border bg-white px-4 py-3 text-sm">
                <div>
                  <p className="font-medium text-gray-900">{a.target_type} — {a.target_id.slice(0, 8)}…</p>
                  <p className="text-xs text-gray-500">Utilisateur : {a.user_id.slice(0, 8)}… · Statut : {a.status}</p>
                  {a.due_date && <p className="text-xs text-gray-500">Échéance : {new Date(a.due_date).toLocaleDateString('fr-FR')}</p>}
                </div>
                <button
                  onClick={() => cancelAssignment(a.id)}
                  disabled={a.status === 'CANCELLED'}
                  className="text-xs text-red-500 hover:underline disabled:opacity-40"
                >
                  Annuler
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
