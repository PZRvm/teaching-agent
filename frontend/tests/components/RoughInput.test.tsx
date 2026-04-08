import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import RoughInput from '../../src/components/RoughInput'

describe('RoughInput', () => {
  it('renders an input element', () => {
    render(<RoughInput />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('passes through placeholder prop', () => {
    render(<RoughInput placeholder="your@email.com" />)
    expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument()
  })

  it('passes through type prop', () => {
    const { container } = render(<RoughInput type="password" />)
    const input = container.querySelector('input')
    expect(input).toHaveAttribute('type', 'password')
  })

  it('passes through value prop', () => {
    render(<RoughInput value="test value" readOnly />)
    expect(screen.getByDisplayValue('test value')).toBeInTheDocument()
  })

  it('applies white background', () => {
    const { container } = render(<RoughInput />)
    const el = container.firstElementChild as HTMLInputElement
    const style = window.getComputedStyle(el)
    expect(style.background).toContain('rgb(255, 255, 255)')
  })

  it('applies 3px solid border', () => {
    const { container } = render(<RoughInput />)
    const el = container.firstElementChild as HTMLInputElement
    const style = window.getComputedStyle(el)
    expect(style.borderWidth).toBe('3px')
    expect(style.borderStyle).toBe('solid')
  })

  it('applies hard box-shadow', () => {
    const { container } = render(<RoughInput />)
    const el = container.firstElementChild as HTMLInputElement
    const style = window.getComputedStyle(el)
    expect(style.boxShadow).toContain('2px 2px 0px 0px')
  })

  it('applies padding', () => {
    const { container } = render(<RoughInput />)
    const el = container.firstElementChild as HTMLInputElement
    const style = window.getComputedStyle(el)
    expect(style.paddingTop).toBe('12px')
    expect(style.paddingRight).toBe('16px')
    expect(style.paddingBottom).toBe('12px')
    expect(style.paddingLeft).toBe('16px')
  })

  it('applies 16px font-size', () => {
    const { container } = render(<RoughInput />)
    const el = container.firstElementChild as HTMLInputElement
    const style = window.getComputedStyle(el)
    expect(style.fontSize).toBe('16px')
  })
})
