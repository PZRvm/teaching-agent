import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import NotFoundPage from '../../src/views/NotFoundPage'

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <NotFoundPage />
    </MemoryRouter>,
  )
}

describe('NotFoundPage', () => {
  it('renders 404 code', () => {
    renderWithRouter()
    expect(screen.getByLabelText('404')).toBeInTheDocument()
  })

  it('renders title and description', () => {
    renderWithRouter()
    expect(screen.getByText('页面未找到')).toBeInTheDocument()
    expect(screen.getByText(/看起来你迷路了/)).toBeInTheDocument()
  })

  it('navigates to home when clicking the button', async () => {
    const user = userEvent.setup()
    renderWithRouter()
    const button = screen.getByText('返回首页 →')
    expect(button).toBeInTheDocument()
    await user.click(button)
  })
})
