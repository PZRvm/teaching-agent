// frontend/tests/hooks/useSessionMessages.test.ts
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import type { WsMessageEvent } from '../../src/types/observation'

vi.mock('../../src/apis/session', () => ({
  getSessionMessages: vi.fn(),
}))

import { useSessionMessages } from '../../src/hooks/useSessionMessages'
import { getSessionMessages } from '../../src/apis/session'

const mockGetSessionMessages = vi.mocked(getSessionMessages)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useSessionMessages', () => {
  it('loads history messages on mount', async () => {
    const historyMessages = [
      {
        id: 1,
        session_id: 1,
        sender: 'teacher',
        message_type: 'lecture',
        content: 'Hello',
        receiver: 'all',
        timestamp: '2026-04-12T10:00:00',
      },
    ]
    mockGetSessionMessages.mockResolvedValueOnce(historyMessages)

    const { result } = renderHook(() => useSessionMessages(1, []))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0].sender).toBe('teacher')
    expect(result.current.messages[0].id).toBe(1)
  })

  it('appends ws messages after history', async () => {
    mockGetSessionMessages.mockResolvedValueOnce([])

    const { result, rerender } = renderHook(
      ({ wsMessages }) => useSessionMessages(1, wsMessages),
      { initialProps: { wsMessages: [] as WsMessageEvent[] } },
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    rerender({
      wsMessages: [
        {
          type: 'message' as const,
          session_id: 1,
          sender: 'student1',
          message_type: 'answer_to_checkpoint',
          content: 'My answer',
          receiver: 'teacher',
          timestamp: '2026-04-12T10:01:00',
        },
      ],
    })

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0].sender).toBe('student1')
  })

  it('deduplicates overlapping messages by triple match', async () => {
    const historyMessages = [
      {
        id: 1,
        session_id: 1,
        sender: 'teacher',
        message_type: 'lecture',
        content: 'Hello world',
        receiver: 'all',
        timestamp: '2026-04-12T10:00:00',
      },
    ]
    mockGetSessionMessages.mockResolvedValueOnce(historyMessages)

    const { result, rerender } = renderHook(
      ({ wsMessages }) => useSessionMessages(1, wsMessages),
      { initialProps: { wsMessages: [] as WsMessageEvent[] } },
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    // WS message duplicates last history message
    rerender({
      wsMessages: [
        {
          type: 'message' as const,
          session_id: 1,
          sender: 'teacher',
          message_type: 'lecture',
          content: 'Hello world',
          receiver: 'all',
          timestamp: '2026-04-12T10:00:00',
        },
      ],
    })

    expect(result.current.messages).toHaveLength(1)
  })

  it('keeps ws messages with newer timestamps', async () => {
    const historyMessages = [
      {
        id: 1,
        session_id: 1,
        sender: 'teacher',
        message_type: 'lecture',
        content: 'Old message',
        receiver: 'all',
        timestamp: '2026-04-12T10:00:00',
      },
    ]
    mockGetSessionMessages.mockResolvedValueOnce(historyMessages)

    const { result, rerender } = renderHook(
      ({ wsMessages }) => useSessionMessages(1, wsMessages),
      { initialProps: { wsMessages: [] as WsMessageEvent[] } },
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    rerender({
      wsMessages: [
        {
          type: 'message' as const,
          session_id: 1,
          sender: 'student1',
          message_type: 'answer_to_checkpoint',
          content: 'New answer',
          receiver: 'teacher',
          timestamp: '2026-04-12T10:01:00',
        },
      ],
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1].content).toBe('New answer')
  })

  it('returns empty messages for invalid sessionId', async () => {
    const { result } = renderHook(() => useSessionMessages(-1, []))

    expect(mockGetSessionMessages).not.toHaveBeenCalled()
    expect(result.current.loading).toBe(false)
    expect(result.current.messages).toHaveLength(0)
  })

  it('returns empty messages for sessionId=0 (boundary)', async () => {
    const { result } = renderHook(() => useSessionMessages(0, []))

    expect(mockGetSessionMessages).not.toHaveBeenCalled()
    expect(result.current.loading).toBe(false)
    expect(result.current.messages).toHaveLength(0)
  })

  it('sets error state on API failure', async () => {
    mockGetSessionMessages.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useSessionMessages(1, []))

    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Network error')
    expect(result.current.messages).toHaveLength(0)
  })

  it('deduplicates ws messages without timestamps by triple match', async () => {
    const historyMessages = [
      {
        id: 1,
        session_id: 1,
        sender: 'teacher',
        message_type: 'lecture',
        content: 'Hello',
        receiver: 'all',
        timestamp: '2026-04-12T10:00:00',
      },
    ]
    mockGetSessionMessages.mockResolvedValueOnce(historyMessages)

    const { result, rerender } = renderHook(
      ({ wsMessages }) => useSessionMessages(1, wsMessages),
      { initialProps: { wsMessages: [] as WsMessageEvent[] } },
    )

    await waitFor(() => expect(result.current.loading).toBe(false))

    rerender({
      wsMessages: [
        {
          type: 'message' as const,
          session_id: 1,
          sender: 'teacher',
          message_type: 'lecture',
          content: 'Hello',
          receiver: 'all',
        },
      ],
    })

    expect(result.current.messages).toHaveLength(1)
  })
})
