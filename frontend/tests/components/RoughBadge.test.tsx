import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import RoughBadge from '../../src/components/RoughBadge'

describe('RoughBadge', () => {
  it('renders children', () => {
    render(<RoughBadge>BETA v0.8.2</RoughBadge>)
    expect(screen.getByText('BETA v0.8.2')).toBeInTheDocument()
  })

  it('applies pink variant background by default', () => {
    const { container } = render(<RoughBadge>badge</RoughBadge>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.background).toContain('rgb(252, 228, 236)')
  })

  it('applies correct variant background colors', () => {
    const variants = [
      { variant: 'pink' as const, rgb: 'rgb(252, 228, 236)' },
      { variant: 'yellow' as const, rgb: 'rgb(255, 249, 196)' },
      { variant: 'blue' as const, rgb: 'rgb(227, 242, 253)' },
      { variant: 'green' as const, rgb: 'rgb(232, 245, 233)' },
    ]

    for (const { variant, rgb } of variants) {
      const { container } = render(<RoughBadge variant={variant}>badge</RoughBadge>)
      const el = container.firstElementChild as HTMLElement
      const style = window.getComputedStyle(el)
      expect(style.background).toContain(rgb)
    }
  })

  it('applies default rotation of 2deg', () => {
    const { container } = render(<RoughBadge>badge</RoughBadge>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.transform).toContain('rotate(2deg)')
  })

  it('applies custom rotation', () => {
    const { container } = render(<RoughBadge rotation={-1}>badge</RoughBadge>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.transform).toContain('rotate(-1deg)')
  })

  it('applies 2px solid border', () => {
    const { container } = render(<RoughBadge>badge</RoughBadge>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.borderWidth).toBe('2px')
    expect(style.borderStyle).toBe('solid')
  })

  it('applies hard box-shadow', () => {
    const { container } = render(<RoughBadge>badge</RoughBadge>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.boxShadow).toContain('2px 2px 0px 0px')
  })

  it('applies bold font-weight', () => {
    const { container } = render(<RoughBadge>badge</RoughBadge>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.fontWeight).toBe('700')
  })

  it('applies 12px font-size', () => {
    const { container } = render(<RoughBadge>badge</RoughBadge>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.fontSize).toBe('12px')
  })
})
