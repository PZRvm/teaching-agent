// frontend/tests/views/ObservationView.test.tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ObservationView from '../../src/views/ObservationView'

const mockNavigate = vi.fn()

// Mock useWebSocket
const mockWsReturn = {
  connectionState: 'connected',
  messages: [],
  checkpointState: null,
  sessionEnded: false,
  teachingMode: 'heuristic',
}

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ sessionId: '42' }),
  }
})

vi.mock('../../src/hooks/useWebSocket', () => ({
  useWebSocket: () => mockWsReturn,
}))

vi.mock('../../src/hooks/useElapsedTime', () => ({
  useElapsedTime: () => '00:00',
}))

describe('ObservationView', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    mockWsReturn.connectionState = 'connected'
    mockWsReturn.messages = []
    mockWsReturn.checkpointState = null
    mockWsReturn.sessionEnded = false
    mockWsReturn.teachingMode = 'heuristic'
  })

  function renderView(sessionId = '42') {
    return render(
      <MemoryRouter initialEntries={[`/observation/session/${sessionId}`]}>
        <ObservationView />
      </MemoryRouter>,
    )
  }

  it('renders page title', () => {
    renderView()
    expect(screen.getByText('观察模式 - 实时观察')).toBeInTheDocument()
  })

  it('displays teaching mode badge when available', () => {
    renderView()
    expect(screen.getByText('启发式')).toBeInTheDocument()
  })

  it('displays elapsed time', () => {
    renderView()
    expect(screen.getByText('已进行')).toBeInTheDocument()
    expect(screen.getByText('00:00')).toBeInTheDocument()
  })

  it('displays message count', () => {
    renderView()
    expect(screen.getByText(/消息：0/)).toBeInTheDocument()
  })

  it('renders empty state when no messages', () => {
    renderView()
    expect(screen.getByText('暂无消息')).toBeInTheDocument()
  })

  it('renders messages from WebSocket', () => {
    mockWsReturn.messages = [
      { type: 'message', session_id: 42, sender: 'teacher', message_type: 'lecture', content: '今天我们学习Python变量' },
    ]
    renderView()
    expect(screen.getByText('今天我们学习Python变量')).toBeInTheDocument()
  })

  it('displays checkpoint state when available', () => {
    mockWsReturn.checkpointState = {
      index: 0,
      checkpoint: { title: 'Python简介', state: 'teaching', key_point: '基础语法' },
      progress: { current: 1, total: 5, completed: 0 },
    }
    renderView()
    expect(screen.getByText('Python简介')).toBeInTheDocument()
    expect(screen.getByText('1/5')).toBeInTheDocument()
  })

  it('shows session ended banner when sessionEnded is true', () => {
    mockWsReturn.sessionEnded = true
    renderView()
    expect(screen.getByText(/会话已结束/)).toBeInTheDocument()
  })

  it('has a back button', () => {
    renderView()
    expect(screen.getByRole('button', { name: '← 返回' })).toBeInTheDocument()
  })
})
