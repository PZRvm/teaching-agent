import { describe, expect, it, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from '../../src/views/LandingPage'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom',
  )
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('LandingPage', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })
  it('renders title, subtitle and both mode cards', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )

    // 主标题 & 副标题
    expect(screen.getByRole('heading', { name: '教学智能体' })).toBeInTheDocument()
    expect(screen.getByText('多Agent教学模拟系统')).toBeInTheDocument()

    // 观察模式卡片
    expect(screen.getByText('观察模式')).toBeInTheDocument()
    expect(
      screen.getByText(
        '进入旁观席位，观察多个AI智能体在模拟课堂中的实时互动、逻辑推演与反馈循环。深入剖析Agent间的协同机制与知识传递路径。',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '开始观察 →' })).toBeInTheDocument()

    // 教师模式卡片
    expect(screen.getByText('教师模式')).toBeInTheDocument()
    expect(
      screen.getByText(
        '扮演引导者角色，直接参与教学模拟。设定教学目标，干预Agent学习进程，并在高保真模拟环境中验证您的教学策略与课程设计。',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '开始教学 →' })).toBeInTheDocument()

    // 底部技术栈说明（文本分散在多个 span 中，使用函数匹配器）
    expect(
      screen.getByText((_content, element) => {
        return element?.tagName === 'P' && /技术栈/.test(element.textContent ?? '')
      }),
    ).toBeInTheDocument()
  })

  it('navigates to observation config when clicking 开始观察', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    await user.click(screen.getByRole('button', { name: '开始观察 →' }))
    expect(mockNavigate).toHaveBeenCalledWith('/observation/config')
  })

  it('navigates to teacher config when clicking 开始教学', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    await user.click(screen.getByRole('button', { name: '开始教学 →' }))
    expect(mockNavigate).toHaveBeenCalledWith('/teacher/config')
  })

  it('navigates to history page when clicking history icon', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )
    await user.click(screen.getByLabelText('教学历史'))
    expect(mockNavigate).toHaveBeenCalledWith('/history')
  })

  it('uses rough design elements like tape, decorations, and footer tags', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )

    expect(document.querySelectorAll('.tape').length).toBeGreaterThanOrEqual(1)
    expect(document.querySelectorAll('.card-decoration').length).toBeGreaterThanOrEqual(1)
    expect(document.querySelectorAll('.footer-tag').length).toBeGreaterThanOrEqual(1)
    expect(document.querySelector('.brand-name')?.textContent).toBe('SimuSketch')
    expect(document.querySelector('.bg-decoration-left')).toBeInTheDocument()
  })
})
