# 前端自动化测试文档

本文档详细描述前端测试体系。

## 测试框架

| 框架/库 | 版本 | 用途 |
|---------|------|------|
| vitest | 2.1+ | 测试运行器（与 Vite 深度集成） |
| @testing-library/react | 16.2+ | React 组件测试 |
| @testing-library/user-event | 14.5+ | 用户交互模拟 |
| @testing-library/jest-dom | 6.6+ | DOM 断言 |
| jsdom | 26.0+ | 浏览器环境模拟 |

## 测试文件结构

```
frontend/
├── src/
│   └── __tests__/           # 组件测试
│       ├── components/      # 组件测试
│       │   ├── ObservationConfig.test.tsx
│       │   ├── ObservationView.test.tsx
│       │   ├── TeacherConfig.test.tsx
│       │   ├── TeacherView.test.tsx
│       │   └── AnalysisReport.test.tsx
│       ├── hooks/           # 自定义 hooks 测试
│       │   ├── useWebSocket.test.ts
│       │   └── useTeachingSession.test.ts
│       └── utils/           # 工具函数测试
│           └── api.test.ts
└── vitest.config.ts        # Vitest 配置
```

## 运行前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行测试并监听文件变化
npm run test:watch

# 运行测试并生成覆盖率报告
npm run test:coverage

# 运行测试 UI 界面
npm run test:ui

# 运行特定测试文件
npm test -- ObservationConfig.test.tsx

# 运行匹配模式的测试
npm test -- --grep "Observation"
```

---

## 待实现的测试

### 组件测试

#### ObservationConfig.test.tsx
观察模式配置组件测试：
- 渲染教学模式选择
- 学生配置方式切换
- 表单验证
- "开始观察"按钮状态

#### ObservationView.test.tsx
观察模式视图组件测试：
- 实时消息列表显示
- 当前模式徽章
- 已进行时间显示
- 消息数量统计

#### TeacherConfig.test.tsx
教师模式配置组件测试：
- 复用 StudentFactory 配置
- 表单验证

#### TeacherView.test.tsx
教师模式视图组件测试：
- 用户输入区域
- 学生响应显示
- 消息列表复用

#### AnalysisReport.test.tsx
分析报告组件测试：
- 课程配置摘要
- 量化指标卡片
- 学生个体统计

### Hooks 测试

#### useWebSocket.test.ts
WebSocket 连接 hook 测试：
- 连接建立
- 消息接收
- 断线处理
- 重连逻辑

#### useTeachingSession.test.ts
教学会话 hook 测试：
- 会话创建
- 状态更新
- 会话结束

---

## 前端测试示例

### 组件测试示例

```typescript
// src/__tests__/components/ObservationConfig.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ObservationConfig from '../components/ObservationConfig'

describe('ObservationConfig', () => {
  it('renders teaching mode selection', () => {
    render(<ObservationConfig />)
    expect(screen.getByText(/教学模式/)).toBeInTheDocument()
  })

  it('enables start button when form is valid', async () => {
    const user = userEvent.setup()
    const mockOnStart = vi.fn()

    render(<ObservationConfig onStart={mockOnStart} />)

    // 填写教学主题
    const topicInput = screen.getByLabelText('教学主题')
    await user.type(topicInput, 'Python 基础')

    // 选择教学模式
    const modeSelect = screen.getByLabelText('教学模式')
    await user.selectOptions(modeSelect, 'didactic')

    // 验证按钮可用
    const startButton = screen.getByText('开始观察')
    expect(startButton).toBeEnabled()

    // 点击按钮
    await user.click(startButton)
    expect(mockOnStart).toHaveBeenCalled()
  })

  it('validates empty topic', async () => {
    const user = userEvent.setup()
    render(<ObservationConfig />)

    const startButton = screen.getByText('开始观察')
    await user.click(startButton)

    expect(await screen.findByText('请输入教学主题'))).toBeInTheDocument()
  })
})
```

### Hook 测试示例

```typescript
// src/__tests__/hooks/useWebSocket.test.ts
import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWebSocket } from '../hooks/useWebSocket'

describe('useWebSocket', () => {
  beforeEach(() => {
    // Mock WebSocket
    global.WebSocket = vi.fn().mockImplementation(() => ({
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  })

  it('connects to WebSocket with correct URL', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/123'))
    
    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/123')
  })

  it('receives and parses messages', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8000/ws/123'))
    
    const ws = global.WebSocket.mock.results[0].value
    
    // 模拟接收消息
    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify({ sender: 'teacher', content: 'Hello' })
    })
    
    ws.addEventListener.mock.calls[0][1](messageEvent)
    
    await waitFor(() => {
      expect(result.current.messages).toEqual([{ sender: 'teacher', content: 'Hello' }])
    })
  })
})
```

### API 测试示例

```typescript
// src/__tests__/utils/api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { http } from 'msw'
import { setupServer } from 'msw/node'
import { createSession } from '../utils/api'

const server = setupServer(
  http.post('/api/sessions', async ({ request }) => {
    return HttpResponse.json({
      id: 1,
      teaching_mode: 'didactic',
      topic: 'Test',
    })
  })
)

describe('createSession', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('creates a new teaching session', async () => {
    const response = await createSession({
      teaching_mode: 'didactic',
      topic: 'Test',
      students_config: { source: 'random' },
    })

    expect(response).toEqual({
      id: 1,
      teaching_mode: 'didactic',
      topic: 'Test',
    })
  })
})
```

---

## 测试覆盖率目标

| 类型 | 目标覆盖率 | 状态 |
|------|-----------|------|
| 组件 | >70% | 🚧 待实现 |
| Hooks | >80% | 🚧 待实现 |
| 工具函数 | >60% | 🚧 待实现 |
| **总体** | **>60%** | **🚧 待实现** |

---

## 常见问题

### Q: 测试中找不到组件样式？

**原因**: `styled-components` 在测试环境中可能未正确处理。

**解决**: 配置 vitest 使用 jsdom 和正确的 transformers：
```typescript
// vitest.config.ts
export default defineConfig({
  css: {
    modules: {
      '.*': 'null-loader',
    },
  },
})
```

### Q: 测试中 `useWebSocket` 报错？

**原因**: 测试环境中没有 WebSocket API。

**解决**: Mock WebSocket：
```typescript
vi.stubGlobal('WebSocket', class {
  addEventListener = vi.fn()
  removeEventListener = vi.fn()
  send = vi.fn()
  close = vi.fn()
})
```

### Q: 测试运行很慢？

**原因**: 每次测试都重新渲染整个组件树。

**解决方案**:
1. 使用 `@testing-library/react` 的 `render` 只渲染必要部分
2. 使用 `vi.mock()` mock 重型依赖
3. 并行运行测试：`vitest --threads`

### Q: TypeScript 类型错误？

**原因**: vitest 的类型定义问题。

**解决**: 确保 `tsconfig.json` 和 `vitest.config.ts` 配置正确：
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
```
