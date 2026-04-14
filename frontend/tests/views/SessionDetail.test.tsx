// frontend/tests/views/SessionDetail.test.tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SessionDetail from '../../src/views/SessionDetail'

const mockNavigate = vi.fn()
const mockGetSessionDetail = vi.fn()
const mockGetSessionMessages = vi.fn()
const mockGetCheckpointPlan = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../src/apis/session', () => ({
  getSessionDetail: (...args: unknown[]) => mockGetSessionDetail(...args),
  getSessionMessages: (...args: unknown[]) => mockGetSessionMessages(...args),
}))

vi.mock('../../src/apis/observation', () => ({
  getCheckpointPlan: (...args: unknown[]) => mockGetCheckpointPlan(...args),
}))

const mockSession = {
  id: 1,
  topic: 'Python 变量与数据类型',
  teaching_mode: 'heuristic',
  status: 'completed',
  start_time: '2026-04-12T14:00:00+08:00',
  end_time: '2026-04-12T15:00:00+08:00',
  duration_seconds: 3600,
  student_count: 3,
  checkpoint_progress: { total: 4, completed: 2, current_index: 2 },
}

const mockMessages = [
  {
    id: 1,
    session_id: 1,
    sender: '教师',
    message_type: 'LECTURE',
    content: '今天我们来学习Python变量。',
    receiver: 'all',
    timestamp: '2026-04-12T14:00:10+08:00',
  },
  {
    id: 2,
    session_id: 1,
    sender: '张三',
    message_type: 'ANSWER_TO_CHECKPOINT',
    content: '变量是用来存储数据的容器。',
    receiver: '教师',
    timestamp: '2026-04-12T14:05:00+08:00',
  },
]

const mockCheckpointPlan = {
  topic: 'Python 变量与数据类型',
  teaching_mode: 'heuristic',
  current_index: 2,
  checkpoints: [
    { title: '变量介绍', key_point: '变量赋值', checkpoint_question: '', state: 'complete' },
    { title: '数据类型', key_point: 'int/str/list', checkpoint_question: '', state: 'complete' },
    { title: '运算符', key_point: '算术运算符', checkpoint_question: '', state: 'teaching' },
    { title: '控制流', key_point: 'if/for/while', checkpoint_question: '', state: 'pending' },
  ],
}

beforeEach(() => {
  mockNavigate.mockClear()
  mockGetSessionDetail.mockResolvedValue(mockSession)
  mockGetSessionMessages.mockResolvedValue(mockMessages)
  mockGetCheckpointPlan.mockResolvedValue(mockCheckpointPlan)
})

function renderDetail(sessionId = '1') {
  return render(
    <MemoryRouter initialEntries={[`/history/${sessionId}`]}>
      <Routes>
        <Route path="/history/:sessionId" element={<SessionDetail />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SessionDetail', () => {
  describe('Basic rendering', () => {
    it('shows loading state initially', () => {
      mockGetSessionDetail.mockReturnValue(new Promise(() => {}))
      renderDetail()
      expect(screen.getByText('加载中...')).toBeInTheDocument()
    })

    it('renders session topic and meta info after loading', async () => {
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('Python 变量与数据类型')).toBeInTheDocument()
      })
      expect(screen.getByText('启发式')).toBeInTheDocument()
      expect(screen.getByText('已完成')).toBeInTheDocument()
      expect(screen.getByText(/3 名学生/)).toBeInTheDocument()
    })

    it('renders back button that navigates to history', async () => {
      renderDetail()
      const backBtn = await screen.findByRole('button', { name: /返回历史/ })
      backBtn.click()
      expect(mockNavigate).toHaveBeenCalledWith('/history')
    })
  })

  describe('Message timeline', () => {
    it('renders teacher and student messages', async () => {
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('今天我们来学习Python变量。')).toBeInTheDocument()
      })
      expect(screen.getByText('变量是用来存储数据的容器。')).toBeInTheDocument()
    })

    it('renders sender names', async () => {
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('教师')).toBeInTheDocument()
      })
      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    it('renders message type labels', async () => {
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('讲授')).toBeInTheDocument()
      })
      expect(screen.getByText('回答')).toBeInTheDocument()
    })

    it('shows empty state when no messages', async () => {
      mockGetSessionMessages.mockResolvedValue([])
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('暂无消息记录')).toBeInTheDocument()
      })
    })
  })

  describe('Checkpoint panel', () => {
    it('renders checkpoint list with titles', async () => {
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('变量介绍')).toBeInTheDocument()
      })
      expect(screen.getByText('数据类型')).toBeInTheDocument()
      expect(screen.getByText('运算符')).toBeInTheDocument()
      expect(screen.getByText('控制流')).toBeInTheDocument()
    })

    it('renders panel title', async () => {
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('检查点进度')).toBeInTheDocument()
      })
    })
  })

  describe('Error handling', () => {
    it('shows error when session not found', async () => {
      mockGetSessionDetail.mockRejectedValue(new Error('会话不存在'))
      renderDetail('999')
      await waitFor(() => {
        expect(screen.getByText('会话不存在')).toBeInTheDocument()
      })
    })

    it('shows error message on API failure', async () => {
      mockGetSessionDetail.mockRejectedValue(new Error('网络错误'))
      renderDetail()
      await waitFor(() => {
        expect(screen.getByText('网络错误')).toBeInTheDocument()
      })
    })
  })
})
