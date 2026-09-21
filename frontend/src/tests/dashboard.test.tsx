import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthContext } from '@/lib/auth'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import type { User } from '@/types/auth'

vi.mock('@/features/courses/api', () => ({
  coursesApi: {
    list: vi.fn().mockResolvedValue({
      items: [{ id: 'c1', owner_id: 'user-1', title: 'Course 1' }],
      total: 1, page: 1, per_page: 100,
    }),
  },
}))
vi.mock('@/features/enrollments/api', () => ({
  enrollmentsApi: {
    list: vi.fn().mockResolvedValue([
      { id: 'e1', status: 'IN_PROGRESS' },
      { id: 'e2', status: 'COMPLETED' },
    ]),
  },
}))
vi.mock('@/features/assignments/api', () => ({
  assignmentsApi: { list: vi.fn().mockResolvedValue([]) },
}))
vi.mock('@/features/users/api', () => ({
  usersApi: { list: vi.fn().mockResolvedValue([]) },
}))

function renderDashboard(role: 'ADMIN' | 'USER') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const user: User = {
    id: 'user-1', email: 'u@test.com', first_name: 'Jean', last_name: 'Dupont',
    role, is_active: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
  }
  render(
    <QueryClientProvider client={qc}>
      <AuthContext.Provider value={{ user, isLoading: false, isAuthenticated: true }}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </AuthContext.Provider>
    </QueryClientProvider>,
  )
}

describe('DashboardPage', () => {
  it('affiche les statistiques de base pour un utilisateur standard', async () => {
    renderDashboard('USER')
    expect(await screen.findByText(/Bonjour Jean/)).toBeInTheDocument()
    expect(screen.getByText('Mes cours')).toBeInTheDocument()
    expect(screen.queryByText('Administration')).not.toBeInTheDocument()
  })

  it("affiche la section d'administration pour un ADMIN", async () => {
    renderDashboard('ADMIN')
    expect(await screen.findByText('Administration')).toBeInTheDocument()
  })
})
