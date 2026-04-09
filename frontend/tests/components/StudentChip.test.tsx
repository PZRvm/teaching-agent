// frontend/tests/components/StudentChip.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import StudentChip from '../../src/components/StudentChip'

describe('StudentChip', () => {
  it('renders student name', () => {
    render(<StudentChip name="张三" level="excellent" />)
    expect(screen.getByText('张三')).toBeInTheDocument()
  })

  it('renders level label for excellent', () => {
    render(<StudentChip name="张三" level="excellent" />)
    expect(screen.getByText('优秀')).toBeInTheDocument()
  })

  it('renders level label for average', () => {
    render(<StudentChip name="李四" level="average" />)
    expect(screen.getByText('中等')).toBeInTheDocument()
  })

  it('renders level label for basic', () => {
    render(<StudentChip name="王五" level="basic" />)
    expect(screen.getByText('基础')).toBeInTheDocument()
  })

  it('does not render delete button when onDelete is not provided', () => {
    const { container } = render(<StudentChip name="张三" level="excellent" />)
    expect(container.querySelector('.delete-btn')).toBeNull()
  })

  it('renders delete button when onDelete is provided', () => {
    render(<StudentChip name="张三" level="excellent" onDelete={() => {}} />)
    expect(screen.getByLabelText('删除 张三')).toBeInTheDocument()
  })

  it('calls onDelete when delete button is clicked', async () => {
    const onDelete = vi.fn()
    const user = await import('@testing-library/user-event').then(m => m.default.setup())
    render(<StudentChip name="张三" level="excellent" onDelete={onDelete} />)
    await user.click(screen.getByLabelText('删除 张三'))
    expect(onDelete).toHaveBeenCalledTimes(1)
  })
})
