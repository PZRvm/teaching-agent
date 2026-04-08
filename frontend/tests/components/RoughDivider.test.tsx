import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import RoughDivider from '../../src/components/RoughDivider'

describe('RoughDivider', () => {
  it('renders a div element', () => {
    const { container } = render(<RoughDivider />)
    const el = container.firstElementChild as HTMLElement
    expect(el.tagName).toBe('DIV')
  })

  it('applies 3px solid border-top', () => {
    const { container } = render(<RoughDivider />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.borderTopWidth).toBe('3px')
    expect(style.borderTopStyle).toBe('solid')
  })

  it('applies border color', () => {
    const { container } = render(<RoughDivider />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.borderTopColor).toContain('26, 26, 26')
  })

  it('applies default maxWidth of 100%', () => {
    const { container } = render(<RoughDivider />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.maxWidth).toBe('100%')
  })

  it('applies custom maxWidth', () => {
    const { container } = render(<RoughDivider maxWidth="600px" />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.maxWidth).toBe('600px')
  })

  it('applies skew transform for hand-drawn effect', () => {
    const { container } = render(<RoughDivider />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.transform).toContain('skew')
  })
})
