// frontend/tests/views/ObservationConfig.test.tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import ObservationConfig from '../../src/views/ObservationConfig'

const mockNavigate = vi.fn()
const mockStartObservation = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../src/apis/observation', () => ({
  startObservation: (...args: unknown[]) => mockStartObservation(...args),
}))

beforeEach(() => {
  mockNavigate.mockClear()
  mockStartObservation.mockClear()
})

function renderConfig() {
  return render(
    <MemoryRouter>
      <ObservationConfig />
    </MemoryRouter>,
  )
}

describe('ObservationConfig', () => {
  it('renders page title and three step sections', () => {
    renderConfig()
    expect(screen.getByRole('heading', { name: '观察模式 - 配置' })).toBeInTheDocument()
    expect(screen.getByText('教学主题')).toBeInTheDocument()
    expect(screen.getByText('教学模式')).toBeInTheDocument()
    expect(screen.getByText('学生配置')).toBeInTheDocument()
  })

  it('renders topic input with placeholder', () => {
    renderConfig()
    const input = screen.getByPlaceholderText('例如：Python变量与数据类型')
    expect(input).toBeInTheDocument()
  })

  it('renders three teaching mode buttons', () => {
    renderConfig()
    expect(screen.getByText('灌输式')).toBeInTheDocument()
    expect(screen.getByText('启发式')).toBeInTheDocument()
    expect(screen.getByText('讨论式')).toBeInTheDocument()
  })

  it('defaults to heuristic mode selected', () => {
    renderConfig()
    const heuristicBtn = screen.getByText('启发式').closest('button')
    expect(heuristicBtn?.className).toContain('selected')
  })

  it('switches teaching mode on click', async () => {
    const user = userEvent.setup()
    renderConfig()
    await user.click(screen.getByText('讨论式'))
    const discussionBtn = screen.getByText('讨论式').closest('button')
    expect(discussionBtn?.className).toContain('selected')
  })

  it('renders student name input and add button', () => {
    renderConfig()
    expect(screen.getByPlaceholderText('学生姓名')).toBeInTheDocument()
    expect(screen.getByText('+ 添加学生')).toBeInTheDocument()
  })

  it('adds a student when filling form and clicking add', async () => {
    const user = userEvent.setup()
    renderConfig()
    await user.type(screen.getByPlaceholderText('学生姓名'), '张三')
    await user.click(screen.getByText('+ 添加学生'))
    expect(screen.getByText('张三')).toBeInTheDocument()
  })

  it('removes a student when clicking delete button', async () => {
    const user = userEvent.setup()
    renderConfig()
    await user.type(screen.getByPlaceholderText('学生姓名'), '张三')
    await user.click(screen.getByText('+ 添加学生'))
    expect(screen.getByText('张三')).toBeInTheDocument()

    // StudentChip 的删除按钮 aria-label 是 "删除 张三"
    const deleteButton = screen.getByLabelText('删除 张三')
    await user.click(deleteButton)
    expect(screen.queryByText('张三')).not.toBeInTheDocument()
  })

  it('shows error when submitting without topic', async () => {
    const user = userEvent.setup()
    renderConfig()

    // 先添加一个学生
    await user.type(screen.getByPlaceholderText('学生姓名'), '张三')
    await user.click(screen.getByText('+ 添加学生'))

    await user.click(screen.getByRole('button', { name: '开始观察' }))
    expect(screen.getByText('请输入教学主题')).toBeInTheDocument()
    expect(mockStartObservation).not.toHaveBeenCalled()
  })

  it('shows error when submitting without students', async () => {
    const user = userEvent.setup()
    renderConfig()

    // 输入主题
    await user.type(screen.getByPlaceholderText('例如：Python变量与数据类型'), 'Python基础')
    await user.click(screen.getByRole('button', { name: '开始观察' }))
    expect(screen.getByText('请至少添加一名学生')).toBeInTheDocument()
    expect(mockStartObservation).not.toHaveBeenCalled()
  })

  it('navigates to observation session on successful submit', async () => {
    const user = userEvent.setup()
    mockStartObservation.mockResolvedValueOnce({ session_id: 42, status: 'running' })

    renderConfig()
    await user.type(screen.getByPlaceholderText('例如：Python变量与数据类型'), 'Python基础')
    await user.type(screen.getByPlaceholderText('学生姓名'), '张三')
    await user.click(screen.getByText('+ 添加学生'))
    await user.click(screen.getByRole('button', { name: '开始观察' }))

    // 等待异步操作完成
    expect(mockStartObservation).toHaveBeenCalledTimes(1)
    expect(mockNavigate).toHaveBeenCalledWith('/observation/session/42')
  }, 10_000)

  it('has a back button that navigates to home', async () => {
    const user = userEvent.setup()
    renderConfig()
    await user.click(screen.getByRole('button', { name: '← 返回' }))
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })
})
