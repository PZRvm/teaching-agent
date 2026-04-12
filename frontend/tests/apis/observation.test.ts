// frontend/tests/apis/observation.test.ts
import { describe, expect, it, vi, beforeEach } from 'vitest'
import type { ObservationConfigPayload } from '../../src/types/observation'

// Mock with factory function to avoid hoisting issues
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: vi.fn(),
      get: vi.fn(),
    })),
  },
}))

vi.mock('../../src/apis/base', () => {
  const mockPost = vi.fn()
  const mockGet = vi.fn()
  return {
    api: { post: mockPost, get: mockGet },
    __mockPost: mockPost,
    __mockGet: mockGet,
  }
})

// Import after mocking
import { startObservation, getAnalysisReport } from '../../src/apis/observation'
import { api } from '../../src/apis/base'

// Get mock references
const mockPost = api.post as ReturnType<typeof vi.fn>
const mockGet = api.get as ReturnType<typeof vi.fn>

beforeEach(() => {
  mockPost.mockClear()
  mockGet.mockClear()
})

describe('startObservation', () => {
  it('calls POST /observation/start with correct payload', async () => {
    mockPost.mockResolvedValueOnce({
      data: { session_id: 42, status: 'running' },
    })

    const payload: ObservationConfigPayload = {
      topic: 'Python变量',
      teaching_mode: 'heuristic',
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    }

    const result = await startObservation(payload)

    expect(mockPost).toHaveBeenCalledTimes(1)
    expect(mockPost).toHaveBeenCalledWith('/observation/start', {
      topic: 'Python变量',
      teaching_mode: 'heuristic',
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    })
    expect(result).toEqual({ session_id: 42, status: 'running' })
  })

  it('throws error when response is not ok', async () => {
    const error = new Error('Topic is required')
    error.message = 'Topic is required'
    mockPost.mockRejectedValueOnce(error)

    await expect(startObservation({
      topic: '',
      teaching_mode: 'heuristic',
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    })).rejects.toThrow('Topic is required')
  })
})

describe('getAnalysisReport', () => {
  it('calls GET /observation/:sessionId/report', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        session_id: 42,
        topic: 'Python变量',
        teaching_mode: 'heuristic',
        duration_seconds: 300,
        total_checkpoints: 5,
        completed_checkpoints: 3,
        total_messages: 20,
        teacher_message_count: 10,
        student_message_count: 10,
        interaction_frequency: 0.67,
        student_participation_rate: 0.8,
        average_knowledge_gain: 2.5,
        average_correct_rate: 0.85,
        student_metrics: [],
      },
    })

    const result = await getAnalysisReport(42)

    expect(mockGet).toHaveBeenCalledTimes(1)
    expect(mockGet).toHaveBeenCalledWith('/observation/42/report')
    expect(result.session_id).toBe(42)
    expect(result.topic).toBe('Python变量')
  })

  it('throws error when session not found', async () => {
    const error = new Error('Session not found')
    error.message = 'Session not found'
    mockGet.mockRejectedValueOnce(error)

    await expect(getAnalysisReport(999)).rejects.toThrow('Session not found')
  })
})
