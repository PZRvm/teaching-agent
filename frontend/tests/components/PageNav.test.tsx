// frontend/tests/components/PageNav.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PageNav from '../../src/components/PageNav'

describe('PageNav', () => {
  it('renders title text', () => {
    render(<PageNav title="观察模式 - 配置" />)
    expect(screen.getByText('观察模式 - 配置')).toBeInTheDocument()
  })

  it('renders back button when onBack is provided', () => {
    const onBack = vi.fn()
    render(<PageNav title="测试" onBack={onBack} />)
    expect(screen.getByRole('button', { name: '← 返回' })).toBeInTheDocument()
  })

  it('does not render back button when onBack is not provided', () => {
    render(<PageNav title="测试" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onBack when back button is clicked', async () => {
    const onBack = vi.fn()
    const user = await import('@testing-library/user-event').then(m => m.default.setup())
    render(<PageNav title="测试" onBack={onBack} />)
    await user.click(screen.getByRole('button', { name: '← 返回' }))
    expect(onBack).toHaveBeenCalledTimes(1)
  })

  it('renders right slot content', () => {
    render(
      <PageNav title="测试" right={<span data-testid="badge">标签</span>} />,
    )
    expect(screen.getByTestId('badge')).toBeInTheDocument()
  })

  it('does not render right slot when not provided', () => {
    const { container } = render(<PageNav title="测试" />)
    expect(container.querySelector('.nav-right')).toBeNull()
  })

  it('applies custom backLabel', () => {
    render(<PageNav title="测试" onBack={() => {}} backLabel="返回首页" />)
    expect(screen.getByRole('button', { name: '返回首页' })).toBeInTheDocument()
  })
})
