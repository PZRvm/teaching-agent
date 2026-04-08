import { render } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import RoughTape from '../../src/components/RoughTape'

describe('RoughTape', () => {
  it('renders a div element', () => {
    const { container } = render(<RoughTape position="top-left" />)
    const el = container.firstElementChild as HTMLElement
    expect(el.tagName).toBe('DIV')
  })

  it('applies 64px width and 32px height', () => {
    const { container } = render(<RoughTape position="top-left" />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.width).toBe('64px')
    expect(style.height).toBe('32px')
  })

  it('applies semi-transparent blue background', () => {
    const { container } = render(<RoughTape position="top-left" />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.background).toContain('227, 242, 253')
  })

  it('applies absolute positioning', () => {
    const { container } = render(<RoughTape position="top-left" />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.position).toBe('absolute')
  })

  it('applies top: -16px', () => {
    const { container } = render(<RoughTape position="top-left" />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.top).toBe('-16px')
  })

  it('applies left positioning for top-left', () => {
    const { container } = render(<RoughTape position="top-left" />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.left).toBe('-8px')
  })

  it('applies right positioning for top-right', () => {
    const { container } = render(<RoughTape position="top-right" />)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.right).toBe('-8px')
  })

  it('applies rotation based on position', () => {
    const { container: leftContainer } = render(<RoughTape position="top-left" />)
    const leftEl = leftContainer.firstElementChild as HTMLElement
    const leftStyle = window.getComputedStyle(leftEl)
    expect(leftStyle.transform).toContain('rotate(-15deg)')

    const { container: rightContainer } = render(<RoughTape position="top-right" />)
    const rightEl = rightContainer.firstElementChild as HTMLElement
    const rightStyle = window.getComputedStyle(rightEl)
    expect(rightStyle.transform).toContain('rotate(15deg)')
  })
})
