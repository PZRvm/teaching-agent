// frontend/tests/components/Footer.test.tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import Footer from '../../src/components/Footer'

describe('Footer', () => {
  it('renders tech stack info', () => {
    render(<Footer />)
    expect(screen.getByText(/技术栈/)).toBeInTheDocument()
    expect(screen.getByText('FastAPI')).toBeInTheDocument()
    expect(screen.getByText('React')).toBeInTheDocument()
    expect(screen.getByText('Qwen')).toBeInTheDocument()
    expect(screen.getByText('SQLite')).toBeInTheDocument()
  })

  it('renders beta tag', () => {
    render(<Footer />)
    expect(screen.getByText('BETA v0.8.2')).toBeInTheDocument()
  })

  it('renders AI simulation tag', () => {
    render(<Footer />)
    expect(screen.getByText('AI SIMULATION')).toBeInTheDocument()
  })

  it('renders footer divider', () => {
    const { container } = render(<Footer />)
    expect(container.querySelector('.footer-divider')).toBeInTheDocument()
  })
})
