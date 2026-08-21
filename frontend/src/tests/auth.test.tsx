import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { LoginPage } from '@/features/auth/pages/LoginPage'

const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })

function Wrap({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={qc}><MemoryRouter>{children}</MemoryRouter></QueryClientProvider>
}

describe('LoginPage', () => {
  it('affiche le formulaire de connexion', () => {
    render(<Wrap><LoginPage /></Wrap>)
    expect(screen.getByRole('heading', { name: 'LMS' })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/mot de passe/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /se connecter/i })).toBeInTheDocument()
  })
})
