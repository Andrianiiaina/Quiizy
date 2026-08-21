import { useState } from 'react'
import { assignmentsApi } from '@/features/lms/api'
import { useCourses } from '@/features/courses/hooks/useCourses'
import { useLPs } from '@/features/lms/hooks'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function AssignmentsPage() {
  const qc = useQueryClient()
  const { data: courses } = useCourses()
  const { data: lps } = useLPs()
  const { data: assignments = [], isLoading } = useQuery({ queryKey: ['assignments'], queryFn: assignmentsApi.list })
  const { mutateAsync: createAssignment, isPending } = useMutation({
    mutationFn: assignmentsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assignments'] }),
  })

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
                  <span className="font-medium">{a.target_type}</span> → <span className="font-mono text-xs">{a.target_id.slice(0, 8)}…</span>
                  {a.due_date && <span className="ml-2 text-gray-500">Échéance : {new Date(a.due_date).toLocaleDateString('fr-FR')}</span>}
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${a.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{a.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
