import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CourseForm } from '@/features/courses/components/CourseForm'

vi.mock('@/features/categories/api', () => ({
  categoriesApi: {
    list: vi.fn().mockResolvedValue([
      { id: 'cat-1', name: 'Python', description: null, created_at: '2026-01-01T00:00:00Z' },
    ]),
    create: vi.fn().mockResolvedValue({
      id: 'cat-2', name: 'Data Science', description: null, created_at: '2026-01-02T00:00:00Z',
    }),
  },
}))

import { categoriesApi } from '@/features/categories/api'

function renderForm() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  render(
    <QueryClientProvider client={qc}>
      <CourseForm onSubmit={onSubmit} isPending={false} submitLabel="Créer le cours" />
    </QueryClientProvider>,
  )
  return { onSubmit }
}

describe('CourseForm — création de catégorie inline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('affiche les catégories existantes dans le select', async () => {
    renderForm()
    expect(await screen.findByRole('option', { name: 'Python' })).toBeInTheDocument()
  })

  it('permet de créer une nouvelle catégorie sans quitter le formulaire', async () => {
    const user = userEvent.setup()
    renderForm()

    await user.click(screen.getByRole('button', { name: /nouvelle catégorie/i }))
    const input = screen.getByPlaceholderText('Nom de la nouvelle catégorie')
    await user.type(input, 'Data Science')
    await user.click(screen.getByRole('button', { name: 'Ajouter' }))

    await waitFor(() => {
      expect(categoriesApi.create).toHaveBeenCalled()
    })
    expect(vi.mocked(categoriesApi.create).mock.calls[0][0]).toEqual({ name: 'Data Science' })
    await waitFor(() => {
      expect(screen.queryByPlaceholderText('Nom de la nouvelle catégorie')).not.toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /nouvelle catégorie/i })).toBeInTheDocument()
  })
})
