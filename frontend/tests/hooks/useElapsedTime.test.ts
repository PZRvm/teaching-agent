// frontend/tests/hooks/useElapsedTime.test.ts
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useElapsedTime } from '../../src/hooks/useElapsedTime'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useElapsedTime', () => {
  it('starts at 00:00', () => {
    const { result } = renderHook(() => useElapsedTime(true))
    expect(result.current).toBe('00:00')
  })

  it('does not tick when running is false', () => {
    const { result } = renderHook(() => useElapsedTime(false))
    act(() => vi.advanceTimersByTime(65_000))
    expect(result.current).toBe('00:00')
  })

  it('ticks every second and formats as MM:SS', () => {
    const { result } = renderHook(() => useElapsedTime(true))

    act(() => vi.advanceTimersByTime(1_000))
    expect(result.current).toBe('00:01')

    act(() => vi.advanceTimersByTime(59_000))
    expect(result.current).toBe('01:00')

    act(() => vi.advanceTimersByTime(60_000))
    expect(result.current).toBe('02:00')
  })

  it('stops ticking when running changes to false', () => {
    const { result, rerender } = renderHook(
      ({ running }) => useElapsedTime(running),
      { initialProps: { running: true } },
    )

    act(() => vi.advanceTimersByTime(10_000))
    expect(result.current).toBe('00:10')

    rerender({ running: false })
    act(() => vi.advanceTimersByTime(10_000))
    expect(result.current).toBe('00:10')
  })

  it('resets time when running changes from false to true', () => {
    const { result, rerender } = renderHook(
      ({ running }) => useElapsedTime(running),
      { initialProps: { running: true } },
    )

    act(() => vi.advanceTimersByTime(30_000))
    expect(result.current).toBe('00:30')

    rerender({ running: false })
    rerender({ running: true })
    expect(result.current).toBe('00:00')
  })
})
