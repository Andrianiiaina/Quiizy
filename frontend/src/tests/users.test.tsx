import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { UsersListPage } from '@/features/users/pages/UsersListPage'

vi.mock('@/features/users/api', () => ({
  usersApi: {
    list: vi.fn().mockResolvedValue([
      { id: 'u1', email: 'admin@test.com', first_name: 'Admin', last_name: 'X', role: 'ADMIN', is_active: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' },
      { id: 'u2', email: 'user@test.com', first_name: 'User', last_name: 'Y', role: 'USER', is_active: true, created_at: '2026-01-02T00:00:00Z', updated_at: '2026-01-02T00:00:00Z' },
    ]),
    get: vi.fn(),
  },
}))

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <UsersListPage />
    </QueryClientProvider>,
  )
}

describe('UsersListPage', () => {
  it('affiche la liste des utilisateurs avec leur rôle', async () => {
    renderPage()
    expect(await screen.findByText('admin@test.com')).toBeInTheDocument()
    expect(screen.getByText('user@test.com')).toBeInTheDocument()
    expect(screen.getByText('ADMIN')).toBeInTheDocument()
    expect(screen.getByText('USER')).toBeInTheDocument()
  })
})
