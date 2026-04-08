import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RoughButton from '../../src/components/RoughButton'

describe('RoughButton', () => {
  it('renders children text and handles click', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(<RoughButton onClick={handleClick}>开始观察 →</RoughButton>)

    const button = screen.getByRole('button', { name: '开始观察 →' })
    expect(button).toBeInTheDocument()

    await user.click(button)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
