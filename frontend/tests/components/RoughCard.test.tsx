import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import RoughCard from '../../src/components/RoughCard'

describe('RoughCard', () => {
  it('renders children', () => {
    render(<RoughCard>card content</RoughCard>)
    expect(screen.getByText('card content')).toBeInTheDocument()
  })

  it('applies blue variant background by default', () => {
    const { container } = render(<RoughCard>content</RoughCard>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.background).toContain('rgb(227, 242, 253)')
  })

  it('applies correct variant background colors', () => {
    const variants = [
      { variant: 'blue' as const, rgb: 'rgb(227, 242, 253)' },
      { variant: 'green' as const, rgb: 'rgb(232, 245, 233)' },
      { variant: 'pink' as const, rgb: 'rgb(252, 228, 236)' },
      { variant: 'yellow' as const, rgb: 'rgb(255, 249, 196)' },
      { variant: 'white' as const, rgb: 'rgb(250, 250, 250)' },
    ]

    for (const { variant, rgb } of variants) {
      const { container } = render(<RoughCard variant={variant}>content</RoughCard>)
      const el = container.firstElementChild as HTMLElement
      const style = window.getComputedStyle(el)
      expect(style.background).toContain(rgb)
    }
  })

  it('applies default rotation of -0.5deg', () => {
    const { container } = render(<RoughCard>content</RoughCard>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.transform).toContain('rotate(-0.5deg)')
  })

  it('applies custom rotation', () => {
    const { container } = render(<RoughCard rotation={2}>content</RoughCard>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.transform).toContain('rotate(2deg)')
  })

  it('renders tape element when tape position is specified', () => {
    const { container } = render(<RoughCard tape="top-left">content</RoughCard>)
    const tape = container.querySelector('.tape')
    expect(tape).toBeInTheDocument()
  })

  it('does not render tape when tape is none', () => {
    const { container } = render(<RoughCard tape="none">content</RoughCard>)
    const tape = container.querySelector('.tape')
    expect(tape).not.toBeInTheDocument()
  })

  it('applies position: relative', () => {
    const { container } = render(<RoughCard>content</RoughCard>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.position).toBe('relative')
  })

  it('applies 3px solid border', () => {
    const { container } = render(<RoughCard>content</RoughCard>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.borderWidth).toBe('3px')
    expect(style.borderStyle).toBe('solid')
  })

  it('applies hard box-shadow', () => {
    const { container } = render(<RoughCard>content</RoughCard>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.boxShadow).toContain('4px 4px 0px 0px')
  })
})
