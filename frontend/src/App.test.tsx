import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders landing page title and modes on root route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: '教学智能体' })).toBeInTheDocument()
    expect(screen.getByText('多Agent教学模拟系统')).toBeInTheDocument()
    expect(screen.getByText('观察模式')).toBeInTheDocument()
    expect(screen.getByText('教师模式')).toBeInTheDocument()
  })
})
