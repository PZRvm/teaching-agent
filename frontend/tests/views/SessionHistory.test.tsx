// frontend/tests/views/SessionHistory.test.tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import SessionHistory from '../../src/views/SessionHistory'

const mockNavigate = vi.fn()
const mockGetSessionList = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../src/apis/session', () => ({
  getSessionList: (...args: unknown[]) => mockGetSessionList(...args),
}))

beforeEach(() => {
  mockNavigate.mockClear()
  mockGetSessionList.mockResolvedValue([])
})

function renderHistory() {
  return render(
    <MemoryRouter initialEntries={['/history']}>
      <Routes>
        <Route path="/history" element={<SessionHistory />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('SessionHistory', () => {
  describe('Basic rendering', () => {
    it('shows loading state initially', () => {
      mockGetSessionList.mockReturnValue(new Promise(() => {}))
      renderHistory()
      expect(screen.getByText('加载中...')).toBeInTheDocument()
    })

    it('renders page title', async () => {
      renderHistory()
      await waitFor(() => {
        expect(screen.getByText('课堂历史记录')).toBeInTheDocument()
      })
    })

    it('renders empty state when no sessions', async () => {
      renderHistory()
      await waitFor(() => {
        expect(screen.getByText('还没有课堂记录')).toBeInTheDocument()
      })
      expect(screen.getByText('开始一节观察模式课程，记录将显示在这里')).toBeInTheDocument()
    })

    it('has back button that navigates to home', async () => {
      const user = userEvent.setup()
      renderHistory()
      const backBtn = await screen.findByRole('button', { name: /首页/ })
      await user.click(backBtn)
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  describe('Session cards', () => {
    it('renders session cards with topic and mode', async () => {
      mockGetSessionList.mockResolvedValue([
        {
          id: 1,
          topic: 'Python 基础',
          teaching_mode: 'heuristic',
          status: 'completed',
          start_time: '2026-04-12T14:00:00+08:00',
          end_time: '2026-04-12T15:00:00+08:00',
          duration_seconds: 3600,
          student_count: 3,
          checkpoint_progress: { total: 4, completed: 2, current_index: 2 },
        },
      ])
      renderHistory()
      await waitFor(() => {
        expect(screen.getByText('Python 基础')).toBeInTheDocument()
      })
      expect(screen.getByText('启发式')).toBeInTheDocument()
      expect(screen.getByText('已完成')).toBeInTheDocument()
      expect(screen.getByText(/3 名学生/)).toBeInTheDocument()
    })

    it('navigates to detail on card click', async () => {
      const user = userEvent.setup()
      mockGetSessionList.mockResolvedValue([
        {
          id: 42,
          topic: 'Python 变量',
          teaching_mode: 'didactic',
          status: 'completed',
          start_time: '2026-04-12T14:00:00+08:00',
          end_time: null,
          duration_seconds: null,
          student_count: 2,
          checkpoint_progress: null,
        },
      ])
      renderHistory()
      const card = await screen.findByText('Python 变量')
      await user.click(card)
      expect(mockNavigate).toHaveBeenCalledWith('/history/42')
    })

    it('shows progress bar when checkpoint_progress exists', async () => {
      mockGetSessionList.mockResolvedValue([
        {
          id: 1,
          topic: 'Test',
          teaching_mode: 'heuristic',
          status: 'completed',
          start_time: '2026-04-12T14:00:00+08:00',
          end_time: null,
          duration_seconds: null,
          student_count: 2,
          checkpoint_progress: { total: 4, completed: 2, current_index: 2 },
        },
      ])
      renderHistory()
      await waitFor(() => {
        expect(screen.getByText('2/4 检查点')).toBeInTheDocument()
      })
    })
  })

  describe('Error handling', () => {
    it('shows error message on API failure', async () => {
      mockGetSessionList.mockRejectedValue(new Error('网络错误'))
      renderHistory()
      await waitFor(() => {
        expect(screen.getByText('网络错误')).toBeInTheDocument()
      })
    })
  })
})
