// frontend/tests/apis/session.test.ts
import { describe, expect, it, vi, beforeEach } from 'vitest'

vi.mock('../../src/apis/base', () => {
  const mockGet = vi.fn()
  return {
    api: { get: mockGet },
  }
})

import { api } from '../../src/apis/base'
import { getSessionMessages } from '../../src/apis/session'

const mockGet = api.get as ReturnType<typeof vi.fn>

beforeEach(() => {
  mockGet.mockClear()
})

describe('getSessionMessages', () => {
  it('fetches messages for a session', async () => {
    const mockMessages = [
      {
        id: 1,
        session_id: 1,
        sender: 'teacher',
        message_type: 'lecture',
        content: '今天我们学习 Python 变量',
        receiver: 'all',
        timestamp: '2026-04-12T10:00:00',
      },
      {
        id: 2,
        session_id: 1,
        sender: '张三',
        message_type: 'answer_to_checkpoint',
        content: '变量是存储数据的容器',
        receiver: 'teacher',
        timestamp: '2026-04-12T10:01:00',
      },
    ]
    mockGet.mockResolvedValueOnce({ data: mockMessages })

    const result = await getSessionMessages(1)

    expect(mockGet).toHaveBeenCalledWith('/sessions/1/messages')
    expect(result).toEqual(mockMessages)
    expect(result).toHaveLength(2)
  })

  it('returns empty array when no messages', async () => {
    mockGet.mockResolvedValueOnce({ data: [] })

    const result = await getSessionMessages(1)

    expect(result).toEqual([])
  })

  it('throws on network error', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network error'))

    await expect(getSessionMessages(1)).rejects.toThrow('Network error')
  })
})
