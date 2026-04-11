// frontend/tests/views/ObservationConfig.test.tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
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
  describe('Basic rendering', () => {
    it('renders page title and hero section', () => {
      renderConfig()
      expect(screen.getByRole('heading', { name: '观察模式 - 配置' })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: '观察模式' })).toBeInTheDocument()
      expect(screen.getByText('旁观 AI 教学与多 Agent 互动')).toBeInTheDocument()
    })

    it('renders three step sections', () => {
      renderConfig()
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

    it('has a back button that navigates to home', async () => {
      const user = userEvent.setup()
      renderConfig()
      await user.click(screen.getByRole('button', { name: '← 返回' }))
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  describe('Manual student creation', () => {
    it('renders source tabs with manual as default', () => {
      renderConfig()
      expect(screen.getByText('手动输入')).toBeInTheDocument()
      expect(screen.getByText('随机生成')).toBeInTheDocument()
      expect(screen.getByText('JSON 导入')).toBeInTheDocument()

      const manualTab = screen.getByText('手动输入').closest('button')
      expect(manualTab?.className).toContain('active')
    })

    it('shows add student button and student list in manual mode', () => {
      renderConfig()
      expect(screen.getByText('+ 添加学生')).toBeInTheDocument()
      // Student summary exists
      const summary = screen.getByText((content, element) => {
        return element?.classList.contains('student-summary') || false
      })
      expect(summary).toBeInTheDocument()
      expect(summary).toHaveTextContent(/已添加.*名学生/)
    })

    it('shows manual form when clicking add student button', async () => {
      const user = userEvent.setup()
      renderConfig()

      await user.click(screen.getByText('+ 添加学生'))

      expect(screen.getByText('添加学生')).toBeInTheDocument()
      expect(screen.getByLabelText('姓名 *')).toBeInTheDocument()
      expect(screen.getByLabelText('水平')).toBeInTheDocument()
      expect(screen.getByLabelText('态度')).toBeInTheDocument()
      expect(screen.getByLabelText('学习能力 (1-10)')).toBeInTheDocument()
      expect(screen.getByLabelText('性别')).toBeInTheDocument()
      expect(screen.getByLabelText('背景')).toBeInTheDocument()
      expect(screen.getByLabelText('特殊特质')).toBeInTheDocument()
    })

    it('adds a student with minimal required fields', async () => {
      const user = userEvent.setup()
      renderConfig()

      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('确认添加'))

      expect(screen.getByText('张三')).toBeInTheDocument()
    })

    it('adds a student with all fields', async () => {
      const user = userEvent.setup()
      renderConfig()

      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '李四')
      await user.selectOptions(screen.getByLabelText('水平'), '优秀')
      await user.selectOptions(screen.getByLabelText('态度'), '积极')
      await user.clear(screen.getByLabelText('学习能力 (1-10)'))
      await user.type(screen.getByLabelText('学习能力 (1-10)'), '8')
      await user.selectOptions(screen.getByLabelText('性别'), '男')
      await user.type(screen.getByLabelText('背景'), '编程基础')
      await user.type(screen.getByLabelText('特殊特质'), '认真,勤奋')
      await user.click(screen.getByText('确认添加'))

      expect(screen.getByText('李四')).toBeInTheDocument()
    })

    it('cancels manual form when clicking cancel button', async () => {
      const user = userEvent.setup()
      renderConfig()

      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('取消'))

      expect(screen.queryByText('添加学生')).not.toBeInTheDocument()
      expect(screen.queryByText('张三')).not.toBeInTheDocument()
    })

    it('shows error when adding student without name', async () => {
      const user = userEvent.setup()
      renderConfig()

      await user.click(screen.getByText('+ 添加学生'))
      await user.click(screen.getByText('确认添加'))

      expect(screen.getByText('请输入学生姓名')).toBeInTheDocument()
    })

    it('removes a student when clicking delete button', async () => {
      const user = userEvent.setup()
      renderConfig()

      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('确认添加'))

      expect(screen.getByText('张三')).toBeInTheDocument()

      const deleteButton = screen.getByLabelText('删除 张三')
      await user.click(deleteButton)

      expect(screen.queryByText('张三')).not.toBeInTheDocument()
    })
  })

  describe('Random student generation', () => {
    it('switches to random mode when clicking tab', async () => {
      const user = userEvent.setup()
      renderConfig()

      await user.click(screen.getByText('随机生成'))

      const randomTab = screen.getByText('随机生成').closest('button')
      expect(randomTab?.className).toContain('active')

      expect(screen.getByLabelText('学生数量 (2-50)')).toBeInTheDocument()
      expect(screen.getByLabelText('优秀比例 (%)')).toBeInTheDocument()
      expect(screen.getByLabelText('中等比例 (%)')).toBeInTheDocument()
      expect(screen.getByLabelText('基础比例 (%)')).toBeInTheDocument()
      expect(screen.getByText('生成学生')).toBeInTheDocument()
    })

    it('generates random students with default configuration', async () => {
      const user = userEvent.setup()
      mockStartObservation.mockResolvedValueOnce({ session_id: 42, status: 'running' })

      renderConfig()

      // 输入主题
      await user.type(screen.getByPlaceholderText('例如：Python变量与数据类型'), 'Python基础')

      // 切换到随机生成
      await user.click(screen.getByText('随机生成'))
      await user.click(screen.getByText('生成学生'))

      // 生成后应该自动切换到手动输入标签页
      const manualTab = screen.getByText('手动输入').closest('button')
      expect(manualTab?.className).toContain('active')

      // 应该生成了 10 个学生（默认值）
      const summary = screen.getByText((content, element) => {
        return element?.classList.contains('student-summary') || false
      })
      expect(summary).toHaveTextContent(/已添加.*10.*名学生/)

      // 应该能提交成功
      await user.click(screen.getByRole('button', { name: '开始观察' }))
      expect(mockStartObservation).toHaveBeenCalledTimes(1)
      expect(mockNavigate).toHaveBeenCalledWith('/observation/session/42')
    })

    it('appends randomly generated students to existing ones', async () => {
      const user = userEvent.setup()
      renderConfig()

      // 先手动添加一个学生
      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('确认添加'))

      // 验证有 1 个学生
      let summary = screen.getByText((content, element) => {
        return element?.classList.contains('student-summary') || false
      })
      expect(summary).toHaveTextContent(/已添加.*1.*名学生/)

      // 切换到随机生成
      await user.click(screen.getByText('随机生成'))
      await user.click(screen.getByText('生成学生'))

      // 生成后应该自动切换到手动输入标签页
      const manualTab = screen.getByText('手动输入').closest('button')
      expect(manualTab?.className).toContain('active')

      // 应该有 11 个学生（1 个手动 + 10 个随机生成）
      summary = screen.getByText((content, element) => {
        return element?.classList.contains('student-summary') || false
      })
      expect(summary).toHaveTextContent(/已添加.*11.*名学生/)
    })
  })

  describe('JSON import', () => {
    it('switches to JSON mode when clicking tab', async () => {
      const user = userEvent.setup()
      const { container } = renderConfig()

      await user.click(screen.getByText('JSON 导入'))

      const jsonTab = screen.getByText('JSON 导入').closest('button')
      expect(jsonTab?.className).toContain('active')

      expect(screen.getByText('粘贴 JSON 格式的学生列表：')).toBeInTheDocument()
      expect(container.querySelector('.json-textarea')).toBeInTheDocument()
      expect(screen.getByText('导入')).toBeInTheDocument()
    })

    it('imports students from valid JSON', async () => {
      const user = userEvent.setup()
      const { container } = renderConfig()

      await user.click(screen.getByText('JSON 导入'))

      const jsonTextarea = container.querySelector('.json-textarea') as HTMLTextAreaElement
      const jsonData = '[{"name": "张三", "level": "excellent", "attitude": "active", "learning_ability": 8}, {"name": "李四", "level": "average", "attitude": "neutral", "learning_ability": 5}]'

      // Directly set value and dispatch change event for JSON input
      fireEvent.change(jsonTextarea, { target: { value: jsonData } })
      await user.click(screen.getByText('导入'))

      // 导入后应该自动切换到手动输入标签页
      const manualTab = screen.getByText('手动输入').closest('button')
      expect(manualTab?.className).toContain('active')

      // Check for student summary with 2 students
      const summary = screen.getByText((content, element) => {
        return element?.classList.contains('student-summary') || false
      })
      expect(summary).toHaveTextContent(/已添加.*2.*名学生/)
    })

    it('shows error when importing invalid JSON', async () => {
      const user = userEvent.setup()
      const { container } = renderConfig()

      await user.click(screen.getByText('JSON 导入'))

      const jsonTextarea = container.querySelector('.json-textarea') as HTMLTextAreaElement
      fireEvent.change(jsonTextarea, { target: { value: 'invalid json' } })

      await user.click(screen.getByText('导入'))

      // Check for the json-error div to appear
      const jsonError = container.querySelector('.json-error')
      expect(jsonError).toBeInTheDocument()
      expect(jsonError?.textContent).toMatch(/json/i)
    })

    it('shows error when JSON has less than 2 students', async () => {
      const user = userEvent.setup()
      const { container } = renderConfig()

      await user.click(screen.getByText('JSON 导入'))

      const jsonTextarea = container.querySelector('.json-textarea') as HTMLTextAreaElement
      fireEvent.change(jsonTextarea, { target: { value: '[{"name": "张三"}]' } })

      await user.click(screen.getByText('导入'))

      expect(screen.getByText('至少需要2个学生')).toBeInTheDocument()
    })
  })

  describe('Form submission', () => {
    it('shows error when submitting without topic', async () => {
      const user = userEvent.setup()
      renderConfig()

      // 先添加一个学生
      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('确认添加'))

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

      expect(screen.getByText('请至少添加2名学生')).toBeInTheDocument()
      expect(mockStartObservation).not.toHaveBeenCalled()
    })

    it('shows error when submitting with only 1 student', async () => {
      const user = userEvent.setup()
      renderConfig()

      // 输入主题
      await user.type(screen.getByPlaceholderText('例如：Python变量与数据类型'), 'Python基础')

      // 添加一个学生
      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('确认添加'))

      await user.click(screen.getByRole('button', { name: '开始观察' }))
      expect(screen.getByText('请至少添加2名学生')).toBeInTheDocument()
      expect(mockStartObservation).not.toHaveBeenCalled()
    })

    it('navigates to observation session on successful submit with manual students', async () => {
      const user = userEvent.setup()
      mockStartObservation.mockResolvedValueOnce({ session_id: 42, status: 'running' })

      renderConfig()
      await user.type(screen.getByPlaceholderText('例如：Python变量与数据类型'), 'Python基础')

      // 添加两个学生
      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('确认添加'))

      await user.click(screen.getByText('+ 添加学生'))
      await user.type(screen.getByLabelText('姓名 *'), '李四')
      await user.click(screen.getByText('确认添加'))

      await user.click(screen.getByRole('button', { name: '开始观察' }))

      expect(mockStartObservation).toHaveBeenCalledTimes(1)
      expect(mockNavigate).toHaveBeenCalledWith('/observation/session/42')
    }, 10_000)

    it('handles API error gracefully', async () => {
      const user = userEvent.setup()
      mockStartObservation.mockRejectedValueOnce(new Error('Network error'))

      renderConfig()
      await user.type(screen.getByPlaceholderText('例如：Python变量与数据类型'), 'Python基础')

      // 使用随机生成快速添加学生
      await user.click(screen.getByText('随机生成'))
      await user.click(screen.getByText('生成学生'))

      await user.click(screen.getByRole('button', { name: '开始观察' }))

      await waitFor(() => {
        expect(screen.getByText('启动观察模式失败，请稍后重试')).toBeInTheDocument()
      })
      expect(mockNavigate).not.toHaveBeenCalled()
    })
  })

  describe('Tab switching', () => {
    it('switches between all three tabs', async () => {
      const user = userEvent.setup()
      renderConfig()

      // Start with manual (default)
      expect(screen.getByText('+ 添加学生')).toBeInTheDocument()

      // Switch to random
      await user.click(screen.getByText('随机生成'))
      expect(screen.getByText('生成学生')).toBeInTheDocument()
      expect(screen.queryByText('+ 添加学生')).not.toBeInTheDocument()

      // Switch to JSON
      await user.click(screen.getByText('JSON 导入'))
      expect(screen.getByText('导入')).toBeInTheDocument()
      expect(screen.queryByText('生成学生')).not.toBeInTheDocument()

      // Switch back to manual
      await user.click(screen.getByText('手动输入'))
      expect(screen.getByText('+ 添加学生')).toBeInTheDocument()
      expect(screen.queryByText('导入')).not.toBeInTheDocument()
    })

    it('preserves students when switching tabs', async () => {
      const user = userEvent.setup()
      renderConfig()

      // Add a student in manual mode
      await user.click(screen.getByText('+ 添加学生'))
      // Wait for the manual form to appear
      expect(await screen.findByText('添加学生')).toBeInTheDocument()
      await user.type(screen.getByLabelText('姓名 *'), '张三')
      await user.click(screen.getByText('确认添加'))

      let summary = screen.getByText((content, element) => {
        return element?.classList.contains('student-summary') || false
      })
      expect(summary).toHaveTextContent(/已添加.*1.*名学生/)

      // Switch to random and back
      await user.click(screen.getByText('随机生成'))
      await user.click(screen.getByText('手动输入'))

      summary = screen.getByText((content, element) => {
        return element?.classList.contains('student-summary') || false
      })
      expect(summary).toHaveTextContent(/已添加.*1.*名学生/)
      expect(screen.getByText('张三')).toBeInTheDocument()
    })
  })
})
