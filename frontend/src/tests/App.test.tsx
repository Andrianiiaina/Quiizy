import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

// Smoke test : vérifie que la chaîne Vitest → Testing Library → JSX fonctionne.
// Les tests de composants métier seront ajoutés dans les features/ au fur et à mesure.

function Greeting({ name }: { name: string }) {
  return <p>Bonjour, {name} !</p>
}

describe('infrastructure de tests', () => {
  it('vitest est opérationnel', () => {
    expect(1 + 1).toBe(2)
  })

  it('Testing Library rend un composant React', () => {
    render(<Greeting name="LMS" />)
    expect(screen.getByText('Bonjour, LMS !')).toBeInTheDocument()
  })
})
