import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import HandDrawnUnderline from '../../src/components/HandDrawnUnderline'

describe('HandDrawnUnderline', () => {
  it('renders children', () => {
    render(<HandDrawnUnderline>underlined text</HandDrawnUnderline>)
    expect(screen.getByText('underlined text')).toBeInTheDocument()
  })

  it('applies relative positioning', () => {
    const { container } = render(<HandDrawnUnderline>text</HandDrawnUnderline>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.position).toBe('relative')
  })

  it('applies inline-block display', () => {
    const { container } = render(<HandDrawnUnderline>text</HandDrawnUnderline>)
    const el = container.firstElementChild as HTMLElement
    const style = window.getComputedStyle(el)
    expect(style.display).toBe('inline-block')
  })

  it('injects ::after pseudo-element with underline SVG in stylesheet', () => {
    render(<HandDrawnUnderline>text</HandDrawnUnderline>)
    const styleSheets = document.styleSheets
    let foundAfter = false
    for (let i = 0; i < styleSheets.length; i++) {
      const sheet = styleSheets[i] as CSSStyleSheet
      try {
        for (let j = 0; j < sheet.cssRules.length; j++) {
          const rule = sheet.cssRules[j] as CSSStyleRule
          if (rule.selectorText?.includes('::after') && rule.cssText.includes('stroke')) {
            foundAfter = true
            break
          }
        }
      } catch {
        // cross-origin stylesheets may throw
      }
      if (foundAfter) break
    }
    expect(foundAfter).toBe(true)
  })

  it('uses custom color in SVG stroke', () => {
    render(<HandDrawnUnderline color="b7102a">text</HandDrawnUnderline>)
    const styleSheets = document.styleSheets
    let foundCustomColor = false
    for (let i = 0; i < styleSheets.length; i++) {
      const sheet = styleSheets[i] as CSSStyleSheet
      try {
        for (let j = 0; j < sheet.cssRules.length; j++) {
          const rule = sheet.cssRules[j] as CSSStyleRule
          if (rule.cssText?.includes('b7102a')) {
            foundCustomColor = true
            break
          }
        }
      } catch {
        // cross-origin stylesheets may throw
      }
      if (foundCustomColor) break
    }
    expect(foundCustomColor).toBe(true)
  })
})
