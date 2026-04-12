# Phase 10: 观察模式前端（核心UI）实现计划

> **给 agentic 工作者：** REQUIRED SUB-SKILL：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐条执行本计划。步骤使用复选框（`- [ ]`）语法方便跟踪。

**Goal：** 实现观察模式的完整前端 UI 流程，包括会话配置页面（ObservationConfig）、实时观察页面（ObservationView）、WebSocket hook 和 API 集成，用户能在 3 步内进入观察模式并实时观看 AI agent 自动教学。

**Architecture：** 采用分层架构：底层 `useWebSocketBase` hook 管理 WebSocket 连接与消息分发（含教学模式追踪），`useWebSocket` 作为观察模式 wrapper；中间层 `apis/observation.ts` 封装 REST API 调用；顶层 `ObservationConfig` 视图负责配置表单，`ObservationView` 视图负责实时消息展示和检查点进度。路由通过 `App.tsx` 的 `<Routes>` 配置 `/observation/config` 和 `/observation/session/:sessionId`。所有 UI 组件遵循 rough-design 手绘草图风格，使用 `styled-components` 单 Wrapper 模式。

**Tech Stack：** React 19 + TypeScript + Vite，styled-components，react-router-dom，Vitest + React Testing Library，WebSocket (原生 API)。

---

## 文件结构（File Structure）

本计划会创建/修改的文件如下：

- **已存在（Existing）**
  - `frontend/src/App.tsx` —— 修改为添加观察模式路由
  - `frontend/src/components/RoughButton.tsx` —— 已有，复用
  - `frontend/src/components/RoughInput.tsx` —— 已有，复用
  - `frontend/src/components/RoughCard.tsx` —— 已有，复用
  - `frontend/src/components/RoughBadge.tsx` —— 已有，复用
  - `frontend/src/components/RoughDivider.tsx` —— 已有，复用

> **共享组件说明：** Phase 10 新增 `PageNav` 和 `StudentChip` 共享组件（任务 1.3 和 1.4），供 Phase 12 教师模式复用。现有组件 `RoughButton`、`RoughCard`、`RoughInput`、`RoughBadge`、`RoughDivider` 直接复用。

- **新增（New）**
  - `frontend/src/types/observation.ts` —— 观察模式相关的 TypeScript 类型定义
  - `frontend/src/apis/observation.ts` —— 观察 REST API 客户端
  - `frontend/src/hooks/useWebSocketBase.ts` —— WebSocket 基础 hook（连接管理、消息分发、心跳、教学模式追踪）
  - `frontend/src/hooks/useWebSocket.ts` —— 观察模式 WebSocket wrapper（复用 useWebSocketBase）
  - `frontend/src/hooks/useElapsedTime.ts` —— 已进行时间计时器 hook
  - `frontend/src/views/ObservationConfig.tsx` —— 观察模式配置页面
  - `frontend/src/views/ObservationView.tsx` —— 观察模式实时观察页面
  - `frontend/tests/types/observation.test.ts` —— 类型导出测试
  - `frontend/tests/apis/observation.test.ts` —— API 客户端测试
  - `frontend/tests/hooks/useWebSocketBase.test.ts` —— WebSocket 基础 hook 测试
  - `frontend/tests/hooks/useElapsedTime.test.ts` —— 计时器 hook 测试
  - `frontend/tests/views/ObservationConfig.test.tsx` —— 配置页面测试
  - `frontend/tests/views/ObservationView.test.tsx` —— 观察页面测试
  - `frontend/src/components/PageNav.tsx` —— 页面顶部导航栏（返回按钮 + 标题 + 右侧插槽），观察模式和教师模式共用
  - `frontend/src/components/StudentChip.tsx` —— 学生信息标签（姓名 + 等级），观察模式和教师模式共用
  - `frontend/tests/components/PageNav.test.tsx` —— 导航栏组件测试
  - `frontend/tests/components/StudentChip.test.tsx` —— 学生标签组件测试

---

## 本计划共用的类型定义

以下类型在整个 Phase 10 中共享，在任务 1 中统一定义。

```typescript
// frontend/src/types/observation.ts

/** 教学模式 */
export type TeachingMode = 'didactic' | 'heuristic' | 'discussion'

/** 教学模式中文名映射 */
export const TEACHING_MODE_LABELS: Record<TeachingMode, string> = {
  didactic: '灌输式',
  heuristic: '启发式',
  discussion: '讨论式',
}

/** 学生水平 */
export type StudentLevel = 'excellent' | 'average' | 'basic'

/** 学生态度 */
export type StudentAttitude = 'active' | 'neutral' | 'passive'

/** 学生配置文件（对应后端 StudentProfile） */
export interface StudentProfile {
  name: string
  gender?: string | null
  level: StudentLevel
  attitude: StudentAttitude
  learning_ability: number
  background?: string | null
  special_traits?: string[]
}

/** 观察模式配置（对应后端 ObservationConfig） */
export interface ObservationConfigPayload {
  topic: string
  teaching_mode: TeachingMode
  checkpoint_count: number
  students: StudentProfile[]
}

/** 观察模式启动响应（对应后端 ObservationStartResponse） */
export interface ObservationStartResponse {
  session_id: number
  status: string
}

/** WebSocket 消息类型 */
export type WsMessageType =
  | 'connected'
  | 'message'
  | 'checkpoint_state_change'
  | 'session_state'
  | 'session_end'
  | 'error'
  | 'pong'

/** WebSocket 消息基类 */
export interface WsEvent {
  type: WsMessageType
  session_id: number
}

/** WebSocket 连接确认事件 */
export interface WsConnectedEvent extends WsEvent {
  type: 'connected'
}

/** WebSocket 消息事件（教师讲授/学生回答等） */
export interface WsMessageEvent extends WsEvent {
  type: 'message'
  sender: string
  message_type: string
  content: string
  receiver?: string
}

/** WebSocket 检查点状态变更事件 */
export interface WsCheckpointStateEvent extends WsEvent {
  type: 'checkpoint_state_change'
  index: number
  checkpoint: {
    title: string
    state: string
    key_point: string
  }
  progress: {
    current: number
    total: number
    completed: number
  }
}

/** WebSocket 会话状态事件 */
export interface WsSessionStateEvent extends WsEvent {
  type: 'session_state'
  teaching_mode: string
  phase: string
  checkpoint_index: number
  total_checkpoints: number
}

/** WebSocket 会话结束事件 */
export interface WsSessionEndEvent extends WsEvent {
  type: 'session_end'
  reason: string
}

/** WebSocket 错误事件 */
export interface WsErrorEvent extends WsEvent {
  type: 'error'
  message: string
}

/** 所有 WebSocket 事件联合类型 */
export type WsEventUnion =
  | WsConnectedEvent
  | WsMessageEvent
  | WsCheckpointStateEvent
  | WsSessionStateEvent
  | WsSessionEndEvent
  | WsErrorEvent
  | { type: 'pong' }

/** 检查点状态 */
export type CheckpointState = 'pending' | 'teaching' | 'questions' | 'complete'

/** 检查点信息 */
export interface CheckpointInfo {
  title: string
  state: CheckpointState
  key_point: string
}

/** 检查点进度 */
export interface CheckpointProgress {
  current: number
  total: number
  completed: number
}

/** 检查点状态数据（从 WebSocket 提取） */
export interface CheckpointStateData {
  index: number
  checkpoint: CheckpointInfo
  progress: CheckpointProgress
}
```

---

## 本计划共用的视觉约定

以下约定统一应用于观察模式两个页面，遵循 `docs/frontend-design-prompts/style-guide.md` 和 `02-observation-config.md`、`03-observation-view.md` 设计规范。

### 颜色（对齐 style-guide.md）

- 页面背景：`#FAFAFA`（白板底色）
- 卡片背景：`#FFF9C4`（黄色便签，步骤卡片）
- 教师消息背景：`#E3F2FD`（蓝色便签）
- 学生回答背景：`#FFF9C4`（黄色便签）
- 学生提问背景：`#FFF3E0`（橙色便签）
- 检查点问题背景：`#F3E5F5`（紫色便签）
- 作业相关背景：`#E8F5E9`（绿色便签）
- 结束反馈背景：`#FCE4EC`（粉色便签）
- 文字主色：`#1A1A1A`
- 边框：`2px solid #1A1A1A`
- 硬阴影：`box-shadow: 3px 3px 0px rgba(0, 0, 0, 0.2)`

### 检查点状态色

- PENDING：`#FFE0B2`（浅橙）
- TEACHING：`#BBDEFB`（浅蓝）
- QUESTIONS：`#E1BEE7`（浅紫）
- COMPLETE：`#C8E6C9`（浅绿）

### 教学模式选择卡片

- 灌输式：`#FFF3E0` 背景，`#FB8500` 边框
- 启发式：`#F3E5F5` 背景，`#9D4EDD` 边框
- 讨论式：`#FCE4EC` 背景，`#E63946` 边框

### 导航栏

- 背景：白色半透明 `rgba(250, 250, 250, 0.95)`
- 底部边框：`2px dashed #6C757D`（手绘虚线）
- 左侧：返回按钮
- 中间：页面标题

> 样式书写规则：**所有区域、元素的样式都写在 `Wrapper` 内部，通过 `.xxx { ... }` 多层嵌套完成，不新增其它 styled 组件。**

---

## 任务 1：定义观察模式 TypeScript 类型

目标：创建统一的 TypeScript 类型定义文件，确保前后端数据结构对齐。

**相关文件：**
- 新建：`frontend/src/types/observation.ts`
- 新建：`frontend/tests/types/observation.test.ts`

### 任务 1.1：编写类型导出测试（RED）

- [ ] **步骤 1：创建测试目录和类型测试文件，验证所有类型和常量正确导出**

首先创建测试子目录（如果不存在）：

```bash
mkdir -p frontend/tests/types frontend/tests/apis frontend/tests/hooks
```

新建 `frontend/tests/types/observation.test.ts`：

```typescript
// frontend/tests/types/observation.test.ts
import { describe, expect, it } from 'vitest'
import {
  type StudentProfile,
  type ObservationConfigPayload,
  type WsMessageEvent,
  type WsCheckpointStateEvent,
  type WsSessionEndEvent,
  type CheckpointState,
  type CheckpointStateData,
  TEACHING_MODE_LABELS,
} from '../../src/types/observation'

describe('observation types', () => {
  it('exports TEACHING_MODE_LABELS with correct labels', () => {
    expect(TEACHING_MODE_LABELS.didactic).toBe('灌输式')
    expect(TEACHING_MODE_LABELS.heuristic).toBe('启发式')
    expect(TEACHING_MODE_LABELS.discussion).toBe('讨论式')
  })

  it('TEACHING_MODE_LABELS has exactly 3 entries', () => {
    expect(Object.keys(TEACHING_MODE_LABELS).length).toBe(3)
  })

  it('allows constructing valid StudentProfile objects', () => {
    const student: StudentProfile = {
      name: '张三',
      level: 'excellent',
      attitude: 'active',
      learning_ability: 8,
    }
    expect(student.name).toBe('张三')
    expect(student.learning_ability).toBe(8)
  })

  it('allows constructing valid ObservationConfigPayload', () => {
    const config: ObservationConfigPayload = {
      topic: 'Python变量与数据类型',
      teaching_mode: 'heuristic',
      checkpoint_count: 5,
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    }
    expect(config.topic).toBe('Python变量与数据类型')
    expect(config.students).toHaveLength(1)
  })

  it('allows constructing valid WsMessageEvent', () => {
    const event: WsMessageEvent = {
      type: 'message',
      session_id: 1,
      sender: 'teacher',
      message_type: 'lecture',
      content: '今天我们学习Python变量...',
    }
    expect(event.type).toBe('message')
    expect(event.sender).toBe('teacher')
  })

  it('allows constructing valid WsCheckpointStateEvent', () => {
    const event: WsCheckpointStateEvent = {
      type: 'checkpoint_state_change',
      session_id: 1,
      index: 0,
      checkpoint: { title: 'Python简介', state: 'teaching', key_point: 'Python基础语法' },
      progress: { current: 1, total: 5, completed: 0 },
    }
    expect(event.checkpoint.title).toBe('Python简介')
    expect(event.progress.total).toBe(5)
  })

  it('allows constructing valid WsSessionEndEvent', () => {
    const event: WsSessionEndEvent = {
      type: 'session_end',
      session_id: 1,
      reason: 'all_checkpoints_completed',
    }
    expect(event.reason).toBe('all_checkpoints_completed')
  })

  it('CheckpointState accepts valid states', () => {
    const states: CheckpointState[] = ['pending', 'teaching', 'questions', 'complete']
    expect(states).toHaveLength(4)
  })

  it('CheckpointStateData matches expected shape', () => {
    const data: CheckpointStateData = {
      index: 0,
      checkpoint: { title: 'Test', state: 'pending', key_point: 'test' },
      progress: { current: 1, total: 3, completed: 0 },
    }
    expect(data.index).toBe(0)
    expect(data.progress.current).toBe(1)
  })
})
```

- [ ] **步骤 2：运行测试，确认因模块缺失而失败**

```bash
cd frontend
npm run test -- tests/types/observation.test.ts
```

**预期结果：** 测试失败，报错 `Cannot find module '../../src/types/observation'`。

### 任务 1.2：实现类型定义文件（GREEN）

- [ ] **步骤 3：创建 `frontend/src/types/observation.ts`，包含所有类型和常量**

将"本计划共用的类型定义"中的全部代码写入此文件。

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/types/observation.test.ts
```

**预期结果：** 全部 9 个测试通过。

- [ ] **步骤 5：提交**

```bash
git add frontend/src/types/observation.ts frontend/tests/types/observation.test.ts
git commit -m "feat(observation-frontend): 添加观察模式 TypeScript 类型定义"
```

---

## 任务 1.3：创建 PageNav 组件

> **跨计划共享：** 本任务创建的 `PageNav` 组件同时服务于观察模式（Phase 10）和教师模式（Phase 12）的页面导航栏。

目标：创建可复用的页面顶部导航栏组件，包含返回按钮、页面标题和右侧插槽，统一所有页面的导航栏风格。

**相关文件：**
- 新建：`frontend/src/components/PageNav.tsx`
- 新建：`frontend/tests/components/PageNav.test.tsx`
- 依赖：`RoughButton`（已有）

### 任务 1.3.1：编写 PageNav 失败测试（RED）

- [ ] **步骤 1：创建 PageNav 测试**

新建 `frontend/tests/components/PageNav.test.tsx`：

```typescript
// frontend/tests/components/PageNav.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PageNav from '../../src/components/PageNav'

describe('PageNav', () => {
  it('renders title text', () => {
    render(<PageNav title="观察模式 - 配置" />)
    expect(screen.getByText('观察模式 - 配置')).toBeInTheDocument()
  })

  it('renders back button when onBack is provided', () => {
    const onBack = vi.fn()
    render(<PageNav title="测试" onBack={onBack} />)
    expect(screen.getByRole('button', { name: '← 返回' })).toBeInTheDocument()
  })

  it('does not render back button when onBack is not provided', () => {
    render(<PageNav title="测试" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onBack when back button is clicked', async () => {
    const onBack = vi.fn()
    const user = await import('@testing-library/user-event').then(m => m.default)
    render(<PageNav title="测试" onBack={onBack} />)
    await user.click(screen.getByRole('button', { name: '← 返回' }))
    expect(onBack).toHaveBeenCalledTimes(1)
  })

  it('renders right slot content', () => {
    render(
      <PageNav title="测试" right={<span data-testid="badge">标签</span>} />,
    )
    expect(screen.getByTestId('badge')).toBeInTheDocument()
  })

  it('does not render right slot when not provided', () => {
    const { container } = render(<PageNav title="测试" />)
    expect(container.querySelector('.nav-right')).toBeNull()
  })

  it('applies custom backLabel', () => {
    render(<PageNav title="测试" onBack={() => {}} backLabel="返回首页" />)
    expect(screen.getByRole('button', { name: '返回首页' })).toBeInTheDocument()
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/components/PageNav.test.tsx
```

### 任务 1.3.2：实现 PageNav 组件（GREEN）

- [ ] **步骤 3：创建 `frontend/src/components/PageNav.tsx`**

新建 `frontend/src/components/PageNav.tsx`：

```tsx
// frontend/src/components/PageNav.tsx
import styled from 'styled-components'
import type { ReactNode } from 'react'
import RoughButton from './RoughButton'

interface PageNavProps {
  /** 页面标题 */
  title: string
  /** 返回按钮回调，不传则不显示返回按钮 */
  onBack?: () => void
  /** 返回按钮文字，默认 "← 返回" */
  backLabel?: string
  /** 右侧插槽（badges、actions 等） */
  right?: ReactNode
}

export default function PageNav({ title, onBack, backLabel = '← 返回', right }: PageNavProps) {
  return (
    <Wrapper>
      <div className="nav-left">
        {onBack && (
          <RoughButton variant="outline" onClick={onBack} className="back-btn">
            {backLabel}
          </RoughButton>
        )}
        <h1 className="nav-title">{title}</h1>
      </div>
      {right && <div className="nav-right">{right}</div>}
    </Wrapper>
  )
}

const Wrapper = styled.nav`
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(250, 250, 250, 0.95);
  backdrop-filter: blur(4px);
  border-bottom: 2px solid #1a1a1a;
  box-shadow: 4px 4px 0px 0px #1a1a1a;

  .nav-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .nav-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #1a1c1c;
    margin: 0;
  }

  .nav-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .back-btn {
    padding: 6px 16px;
    font-size: 14px;
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/components/PageNav.test.tsx
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/components/PageNav.tsx frontend/tests/components/PageNav.test.tsx
git commit -m "feat(frontend): 添加 PageNav 页面导航栏共享组件"
```

---

## 任务 1.4：创建 StudentChip 组件

> **跨计划共享：** 本任务创建的 `StudentChip` 组件同时服务于观察模式（Phase 10）和教师模式（Phase 12）的学生配置页面。

目标：创建可复用的学生信息标签组件，显示学生姓名和等级。

**相关文件：**
- 新建：`frontend/src/components/StudentChip.tsx`
- 新建：`frontend/tests/components/StudentChip.test.tsx`
- 依赖：`types/observation.ts`（Task 1 创建）

### 任务 1.4.1：编写 StudentChip 失败测试（RED）

- [ ] **步骤 1：创建 StudentChip 测试**

新建 `frontend/tests/components/StudentChip.test.tsx`：

```typescript
// frontend/tests/components/StudentChip.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import StudentChip from '../../src/components/StudentChip'

describe('StudentChip', () => {
  it('renders student name', () => {
    render(<StudentChip name="张三" level="excellent" />)
    expect(screen.getByText('张三')).toBeInTheDocument()
  })

  it('renders level label for excellent', () => {
    render(<StudentChip name="张三" level="excellent" />)
    expect(screen.getByText('优秀')).toBeInTheDocument()
  })

  it('renders level label for average', () => {
    render(<StudentChip name="李四" level="average" />)
    expect(screen.getByText('中等')).toBeInTheDocument()
  })

  it('renders level label for basic', () => {
    render(<StudentChip name="王五" level="basic" />)
    expect(screen.getByText('基础')).toBeInTheDocument()
  })

  it('does not render delete button when onDelete is not provided', () => {
    const { container } = render(<StudentChip name="张三" level="excellent" />)
    expect(container.querySelector('.delete-btn')).toBeNull()
  })

  it('renders delete button when onDelete is provided', () => {
    render(<StudentChip name="张三" level="excellent" onDelete={() => {}} />)
    expect(screen.getByLabelText('删除 张三')).toBeInTheDocument()
  })

  it('calls onDelete when delete button is clicked', async () => {
    const onDelete = vi.fn()
    const user = await import('@testing-library/user-event').then(m => m.default)
    render(<StudentChip name="张三" level="excellent" onDelete={onDelete} />)
    await user.click(screen.getByLabelText('删除 张三'))
    expect(onDelete).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/components/StudentChip.test.tsx
```

### 任务 1.4.2：实现 StudentChip 组件（GREEN）

- [ ] **步骤 3：创建 `frontend/src/components/StudentChip.tsx`**

新建 `frontend/src/components/StudentChip.tsx`：

```tsx
// frontend/src/components/StudentChip.tsx
import styled from 'styled-components'
import type { StudentLevel } from '../types/observation'

interface StudentChipProps {
  /** 学生姓名 */
  name: string
  /** 学生水平 */
  level: StudentLevel
  /** 删除回调，不传则不显示删除按钮 */
  onDelete?: () => void
}

const LEVEL_LABELS: Record<StudentLevel, string> = {
  excellent: '优秀',
  average: '中等',
  basic: '基础',
}

const LEVEL_COLORS: Record<StudentLevel, { bg: string; color: string }> = {
  excellent: { bg: '#E3F2FD', color: '#1565C0' },
  average: { bg: '#FFF9C4', color: '#F57F17' },
  basic: { bg: '#FFECB3', color: '#E65100' },
}

export default function StudentChip({ name, level, onDelete }: StudentChipProps) {
  const levelColor = LEVEL_COLORS[level]

  return (
    <Wrapper>
      <span className="student-name">{name}</span>
      <span className="student-level" style={{ background: levelColor.bg, color: levelColor.color }}>
        {LEVEL_LABELS[level]}
      </span>
      {onDelete && (
        <button className="delete-btn" onClick={onDelete} aria-label={`删除 ${name}`}>
          ×
        </button>
      )}
    </Wrapper>
  )
}

const Wrapper = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #ffffff;
  border: 2px solid #1a1a1a;
  border-radius: 8px;
  box-shadow: 2px 2px 0px 0px #1a1a1a;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px 0px #1a1a1a;
  }

  .student-name {
    font-weight: 700;
    font-size: 14px;
    color: #1a1c1c;
  }

  .student-level {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
    border: 1px solid rgba(0, 0, 0, 0.1);
  }

  .delete-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: #e63946;
    font-size: 16px;
    padding: 0 2px;
    line-height: 1;

    &:hover {
      transform: scale(1.2);
    }
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/components/StudentChip.test.tsx
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/components/StudentChip.tsx frontend/tests/components/StudentChip.test.tsx
git commit -m "feat(frontend): 添加 StudentChip 学生信息标签共享组件"
```

---

## 任务 1.5：创建 API 基础模块

> **跨计划共享：** 本任务创建的 `apis/base.ts` 同时服务于 Phase 10、11、12 的所有 API 调用。后续计划不再重复创建此文件。

目标：创建前端 API 客户端基础配置，使用 axios 提供统一的 HTTP 请求封装，为后续所有 API 调用提供统一基础。

**相关文件：**
- 新建：`frontend/src/apis/base.ts`

### 任务 1.5.1：实现 API 基础模块

- [ ] **步骤 1：安装 axios 依赖**

```bash
cd frontend
npm install axios
```

- [ ] **步骤 2：创建 `frontend/src/apis/base.ts`**

新建 `frontend/src/apis/base.ts`：

```typescript
// frontend/src/apis/base.ts
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail ?? error.message
    throw new Error(detail)
  },
)
```

- [ ] **步骤 3：确认安装成功**

```bash
cd frontend
npm run lint
```

- [ ] **步骤 4：提交**

```bash
git add frontend/src/apis/base.ts frontend/package.json frontend/package-lock.json
git commit -m "feat(frontend): 添加 API 基础模块（axios 封装）"
```

---

## 任务 2：实现观察模式 REST API 客户端

目标：封装 `POST /observation/start` 的 API 调用，供 ObservationConfig 页面使用。

**相关文件：**
- 新建：`frontend/src/apis/observation.ts`
- 依赖：`frontend/src/apis/base.ts`（任务 1.5 创建）

### 任务 2.1：编写 API 客户端失败测试（RED）

- [ ] **步骤 1：创建 API 客户端测试**

新建 `frontend/tests/apis/observation.test.ts`：

```typescript
// frontend/tests/apis/observation.test.ts
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { startObservation } from '../../src/apis/observation'
import type { ObservationConfigPayload } from '../../src/types/observation'

// Mock axios
const mockPost = vi.fn()

vi.mock('axios', () => ({
  default: {
    create: () => ({ post: mockPost }),
  },
}))

vi.mock('../../src/apis/base', () => ({
  api: { post: mockPost },
}))

beforeEach(() => {
  mockPost.mockClear()
})

describe('startObservation', () => {
  it('calls POST /observation/start with correct payload', async () => {
    mockPost.mockResolvedValueOnce({
      data: { session_id: 42, status: 'running' },
    })

    const payload: ObservationConfigPayload = {
      topic: 'Python变量',
      teaching_mode: 'heuristic',
      checkpoint_count: 5,
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    }

    const result = await startObservation(payload)

    expect(mockPost).toHaveBeenCalledTimes(1)
    expect(mockPost).toHaveBeenCalledWith('/observation/start', {
      topic: 'Python变量',
      teaching_mode: 'heuristic',
      checkpoint_count: 5,
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    })
    expect(result).toEqual({ session_id: 42, status: 'running' })
  })

  it('throws error when response is not ok', async () => {
    mockPost.mockRejectedValueOnce({
      response: { status: 400, data: { detail: 'Topic is required' } },
      message: 'Request failed with status code 400',
    })

    await expect(startObservation({
      topic: '',
      teaching_mode: 'heuristic',
      checkpoint_count: 5,
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    })).rejects.toThrow('Topic is required')
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/apis/observation.test.ts
```

### 任务 2.2：实现 API 客户端（GREEN）

- [ ] **步骤 3：创建 `frontend/src/apis/observation.ts`**

新建 `frontend/src/apis/observation.ts`：

```typescript
// frontend/src/apis/observation.ts
import { api } from './base'
import type {
  ObservationConfigPayload,
  ObservationStartResponse,
} from '../types/observation'

/** 启动观察模式会话 */
export async function startObservation(
  config: ObservationConfigPayload,
): Promise<ObservationStartResponse> {
  const { data } = await api.post<ObservationStartResponse>(
    '/observation/start',
    config,
  )
  return data
}

/** 学生个体指标 */
export interface StudentMetrics {
  student_name: string
  level: string
  attitude: string
  learning_ability: number
  knowledge_gain: number
  final_knowledge_level: number
  message_count: number
  questions_asked: number
  learned_concepts_count: number
}

/** 分析报告响应 */
export interface AnalysisReport {
  session_id: number
  topic: string
  teaching_mode: string
  duration_seconds: number | null
  total_checkpoints: number
  completed_checkpoints: number
  total_messages: number
  teacher_message_count: number
  student_message_count: number
  interaction_frequency: number
  student_participation_rate: number
  average_knowledge_gain: number
  average_correct_rate: number
  student_metrics: StudentMetrics[]
}

/**
 * 获取观察模式分析报告.
 *
 * @param sessionId 会话 ID
 * @returns 分析报告数据
 * @throws 当会话不存在时抛出错误
 */
export async function getAnalysisReport(sessionId: number): Promise<AnalysisReport> {
  const { data } = await api.get<AnalysisReport>(
    `/observation/${sessionId}/report`,
  )
  return data
}
```

> **跨计划说明：** 此文件同时包含 Phase 10 的 `startObservation` 和 Phase 11 的 `getAnalysisReport`。Phase 11 实现时无需再创建此文件。

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/apis/observation.test.ts
```

**预期结果：** 2 个测试全部通过。

- [ ] **步骤 5：提交**

```bash
git add frontend/src/apis/observation.ts frontend/tests/apis/observation.test.ts
git commit -m "feat(observation-frontend): 添加观察模式 REST API 客户端（startObservation + getAnalysisReport）"
```

---

## 任务 3：实现 useWebSocketBase Hook + useWebSocket Wrapper

目标：创建 WebSocket 基础 hook（useWebSocketBase）处理连接、消息接收、断线重连、心跳和教学模式追踪，以及观察模式 wrapper（useWebSocket）。

> **跨计划说明：** `useWebSocketBase` 是核心实现，同时服务于观察模式（Phase 10）和教师模式（Phase 12）。Phase 12 将创建 `useTeacherWebSocket` wrapper，在 base 之上添加 `sendCommand` 等双向通信能力。

**相关文件：**
- 新建：`frontend/src/hooks/useWebSocketBase.ts`
- 新建：`frontend/src/hooks/useWebSocket.ts`（wrapper）
- 新建：`frontend/tests/hooks/useWebSocketBase.test.ts`

### 任务 3.1：编写 useWebSocketBase 失败测试（RED）

- [ ] **步骤 1：创建 useWebSocketBase hook 测试**

新建 `frontend/tests/hooks/useWebSocketBase.test.ts`：

```typescript
// frontend/tests/hooks/useWebSocketBase.test.ts
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import type { WsEventUnion } from '../../src/types/observation'

// 模块级实例追踪，用于在测试中获取创建的 WebSocket 实例
let lastCreatedWs: MockWebSocket | null = null

// WebSocket mock 类
class MockWebSocket {
  static OPEN = 1
  static CLOSED = 3
  static CONNECTING = 0
  readyState = MockWebSocket.CONNECTING
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  send = vi.fn()
  close = vi.fn()

  constructor(public url: string) {
    lastCreatedWs = this
  }

  // 模拟连接成功
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.()
  }

  // 模拟收到消息
  simulateMessage(data: WsEventUnion) {
    this.onmessage?.({ data: JSON.stringify(data) })
  }

  // 模拟连接关闭
  simulateClose() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.()
  }
}

// 保存原始 WebSocket
const OriginalWebSocket = globalThis.WebSocket

beforeEach(() => {
  lastCreatedWs = null
  vi.useFakeTimers()
  // 替换全局 WebSocket
  globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket
})

afterEach(() => {
  vi.useRealTimers()
  globalThis.WebSocket = OriginalWebSocket
})

// 延迟导入 hook（在 WebSocket mock 设置完成后）
async function getHook() {
  return (await import('../../src/hooks/useWebSocketBase')).useWebSocketBase
}

describe('useWebSocketBase', () => {
  it('initializes with connecting state', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    expect(result.current.connectionState).toBe('connecting')
  })

  it('transitions to connected state on open', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))

    // 获取创建的 WebSocket 实例
    const createdWs = lastCreatedWs!
    act(() => createdWs.simulateOpen())

    expect(result.current.connectionState).toBe('connected')
  })

  it('stores received messages in messages array', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    act(() =>
      createdWs.simulateMessage({
        type: 'message',
        session_id: 1,
        sender: 'teacher',
        message_type: 'lecture',
        content: '今天我们学习Python变量...',
      }),
    )

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0].content).toBe('今天我们学习Python变量...')
  })

  it('updates checkpointState on checkpoint_state_change event', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    act(() =>
      createdWs.simulateMessage({
        type: 'checkpoint_state_change',
        session_id: 1,
        index: 0,
        checkpoint: { title: 'Python简介', state: 'teaching', key_point: '基础语法' },
        progress: { current: 1, total: 5, completed: 0 },
      }),
    )

    expect(result.current.checkpointState).not.toBeNull()
    expect(result.current.checkpointState!.checkpoint.title).toBe('Python简介')
    expect(result.current.checkpointState!.progress.total).toBe(5)
  })

  it('sets sessionEnded to true on session_end event', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    expect(result.current.sessionEnded).toBe(false)

    act(() =>
      createdWs.simulateMessage({
        type: 'session_end',
        session_id: 1,
        reason: 'all_checkpoints_completed',
      }),
    )

    expect(result.current.sessionEnded).toBe(true)
  })

  it('updates teachingMode from session_state event', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    expect(result.current.teachingMode).toBeNull()

    act(() =>
      createdWs.simulateMessage({
        type: 'session_state',
        session_id: 1,
        teaching_mode: 'heuristic',
        phase: 'teaching',
        checkpoint_index: 0,
        total_checkpoints: 5,
      }),
    )

    expect(result.current.teachingMode).toBe('heuristic')
  })

  it('closes WebSocket on unmount', async () => {
    const useWebSocketBase = await getHook()
    const { unmount } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())
    unmount()

    expect(createdWs.close).toHaveBeenCalled()
  })

  it('sends ping heartbeat every 30 seconds', async () => {
    const useWebSocketBase = await getHook()
    renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    // 快进 30 秒
    act(() => vi.advanceTimersByTime(30_000))
    expect(createdWs.send).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }))

    // 再快进 30 秒
    act(() => vi.advanceTimersByTime(30_000))
    expect(createdWs.send).toHaveBeenCalledTimes(2)
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/hooks/useWebSocketBase.test.ts
```

### 任务 3.2：实现 useWebSocketBase Hook（GREEN）

- [ ] **步骤 3：创建 `frontend/src/hooks/useWebSocketBase.ts`**

新建 `frontend/src/hooks/useWebSocketBase.ts`：

```typescript
// frontend/src/hooks/useWebSocketBase.ts
import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsEventUnion, WsMessageEvent, CheckpointStateData, TeachingMode } from '../types/observation'

/** WebSocket 连接状态 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected'

/** useWebSocketBase hook 返回值 */
export interface UseWebSocketBaseReturn {
  /** 当前连接状态 */
  connectionState: ConnectionState
  /** 收到的所有消息 */
  messages: WsMessageEvent[]
  /** 当前检查点状态 */
  checkpointState: CheckpointStateData | null
  /** 会话是否已结束 */
  sessionEnded: boolean
  /** 教学模式（从 session_state 事件获取，初始为 null） */
  teachingMode: TeachingMode | null
}

/** WebSocket 基础 hook - 管理连接、消息分发、心跳和教学模式追踪 */
export function useWebSocketBase(sessionId: number): UseWebSocketBaseReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting')
  const [messages, setMessages] = useState<WsMessageEvent[]>([])
  const [checkpointState, setCheckpointState] = useState<CheckpointStateData | null>(null)
  const [sessionEnded, setSessionEnded] = useState(false)
  const [teachingMode, setTeachingMode] = useState<TeachingMode | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const startHeartbeat = useCallback((ws: WebSocket) => {
    // 清除旧的心跳
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
    }
    heartbeatRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30_000)
  }, [])

  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
      heartbeatRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!sessionId) return

    const wsUrl = `ws://localhost:8000/ws/sessions/${sessionId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionState('connected')
      startHeartbeat(ws)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsEventUnion

        switch (data.type) {
          case 'message':
            setMessages((prev) => [...prev, data])
            break
          case 'checkpoint_state_change':
            setCheckpointState({
              index: data.index,
              checkpoint: data.checkpoint,
              progress: data.progress,
            })
            break
          case 'session_state':
            setTeachingMode(data.teaching_mode as TeachingMode)
            break
          case 'session_end':
            setSessionEnded(true)
            break
          case 'pong':
            // 心跳响应，无需处理
            break
          default:
            // connected / error 等事件暂不处理
            break
        }
      } catch {
        // JSON 解析失败，忽略
      }
    }

    ws.onclose = () => {
      setConnectionState('disconnected')
      stopHeartbeat()
    }

    ws.onerror = () => {
      setConnectionState('disconnected')
      stopHeartbeat()
    }

    return () => {
      stopHeartbeat()
      ws.close()
    }
  }, [sessionId, startHeartbeat, stopHeartbeat])

  return { connectionState, messages, checkpointState, sessionEnded, teachingMode }
}
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/hooks/useWebSocketBase.test.ts
```

**预期结果：** 8 个测试全部通过（包含新增的 teachingMode 测试）。

### 任务 3.3：创建 useWebSocket Wrapper

- [ ] **步骤 5：创建 `frontend/src/hooks/useWebSocket.ts`**

新建 `frontend/src/hooks/useWebSocket.ts`：

```typescript
// frontend/src/hooks/useWebSocket.ts
// 观察模式 WebSocket wrapper —— 复用 useWebSocketBase，保持向后兼容
import { useWebSocketBase } from './useWebSocketBase'
import type { UseWebSocketBaseReturn } from './useWebSocketBase'

/** 观察模式 WebSocket hook（只读） */
export function useWebSocket(sessionId: number): UseWebSocketBaseReturn {
  return useWebSocketBase(sessionId)
}
```

- [ ] **步骤 6：提交**

```bash
git add frontend/src/hooks/useWebSocketBase.ts frontend/src/hooks/useWebSocket.ts frontend/tests/hooks/useWebSocketBase.test.ts
git commit -m "feat(observation-frontend): 实现 useWebSocketBase hook + useWebSocket wrapper（含教学模式追踪）"
```

---

## 任务 4：实现 useElapsedTime Hook

目标：创建一个简单的已进行时间计时器 hook，每秒更新一次，显示 `MM:SS` 格式。

**相关文件：**
- 新建：`frontend/src/hooks/useElapsedTime.ts`
- 新建：`frontend/tests/hooks/useElapsedTime.test.ts`

### 任务 4.1：编写 useElapsedTime 失败测试（RED）

- [ ] **步骤 1：创建 useElapsedTime hook 测试**

新建 `frontend/tests/hooks/useElapsedTime.test.ts`：

```typescript
// frontend/tests/hooks/useElapsedTime.test.ts
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useElapsedTime } from '../../src/hooks/useElapsedTime'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useElapsedTime', () => {
  it('starts at 00:00', () => {
    const { result } = renderHook(() => useElapsedTime(true))
    expect(result.current).toBe('00:00')
  })

  it('does not tick when running is false', () => {
    const { result } = renderHook(() => useElapsedTime(false))
    act(() => vi.advanceTimersByTime(65_000))
    expect(result.current).toBe('00:00')
  })

  it('ticks every second and formats as MM:SS', () => {
    const { result } = renderHook(() => useElapsedTime(true))

    act(() => vi.advanceTimersByTime(1_000))
    expect(result.current).toBe('00:01')

    act(() => vi.advanceTimersByTime(59_000))
    expect(result.current).toBe('01:00')

    act(() => vi.advanceTimersByTime(60_000))
    expect(result.current).toBe('02:00')
  })

  it('stops ticking when running changes to false', () => {
    const { result, rerender } = renderHook(
      ({ running }) => useElapsedTime(running),
      { initialProps: { running: true } },
    )

    act(() => vi.advanceTimersByTime(10_000))
    expect(result.current).toBe('00:10')

    rerender({ running: false })
    act(() => vi.advanceTimersByTime(10_000))
    expect(result.current).toBe('00:10')
  })

  it('resets time when running changes from false to true', () => {
    const { result, rerender } = renderHook(
      ({ running }) => useElapsedTime(running),
      { initialProps: { running: true } },
    )

    act(() => vi.advanceTimersByTime(30_000))
    expect(result.current).toBe('00:30')

    rerender({ running: false })
    rerender({ running: true })
    expect(result.current).toBe('00:00')
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/hooks/useElapsedTime.test.ts
```

### 任务 4.2：实现 useElapsedTime Hook（GREEN）

- [ ] **步骤 3：创建 `frontend/src/hooks/useElapsedTime.ts`**

新建 `frontend/src/hooks/useElapsedTime.ts`：

```typescript
// frontend/src/hooks/useElapsedTime.ts
import { useEffect, useState } from 'react'

/** 将秒数格式化为 MM:SS */
function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

/** 已进行时间计时器 hook，每秒更新一次 */
export function useElapsedTime(running: boolean): string {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    if (!running) {
      setSeconds(0)
      return
    }

    setSeconds(0)
    const interval = setInterval(() => {
      setSeconds((prev) => prev + 1)
    }, 1_000)

    return () => clearInterval(interval)
  }, [running])

  return formatTime(seconds)
}
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/hooks/useElapsedTime.test.ts
```

**预期结果：** 5 个测试全部通过。

- [ ] **步骤 5：提交**

```bash
git add frontend/src/hooks/useElapsedTime.ts frontend/tests/hooks/useElapsedTime.test.ts
git commit -m "feat(observation-frontend): 实现 useElapsedTime 计时器 hook"
```

---

## 任务 5：实现 ObservationConfig 视图（配置页面）

目标：实现观察模式配置页面，包含教学主题输入、教学模式选择、学生配置（手动添加）和"开始观察"按钮。配置完成后调用 `POST /observation/start` 并跳转到观察页面。

**相关文件：**
- 新建：`frontend/src/views/ObservationConfig.tsx`
- 新建：`frontend/tests/views/ObservationConfig.test.tsx`

### 任务 5.1：编写 ObservationConfig 失败测试（RED）

- [ ] **步骤 1：创建 ObservationConfig 测试**

新建 `frontend/tests/views/ObservationConfig.test.tsx`：

```typescript
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
    expect(screen.getByRole('heading', { name: '观察模式 - 会话配置' })).toBeInTheDocument()
    expect(screen.getByText(/步骤 1/)).toBeInTheDocument()
    expect(screen.getByText(/步骤 2/)).toBeInTheDocument()
    expect(screen.getByText(/步骤 3/)).toBeInTheDocument()
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

    const deleteButtons = screen.getAllByLabelText('删除学生')
    await user.click(deleteButtons[0])
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
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/views/ObservationConfig.test.tsx
```

### 任务 5.2：实现 ObservationConfig 视图（GREEN）

- [ ] **步骤 3：创建 `frontend/src/views/ObservationConfig.tsx`**

新建 `frontend/src/views/ObservationConfig.tsx`：

```tsx
// frontend/src/views/ObservationConfig.tsx
import { useState } from 'react'
import styled from 'styled-components'
import { useNavigate } from 'react-router-dom'
import PageNav from '../components/PageNav'
import StudentChip from '../components/StudentChip'
import RoughButton from '../components/RoughButton'
import RoughInput from '../components/RoughInput'
import type { TeachingMode, StudentProfile, StudentLevel, StudentAttitude } from '../types/observation'
import { TEACHING_MODE_LABELS } from '../types/observation'
import { startObservation } from '../apis/observation'

const TEACHING_MODES: { value: TeachingMode; icon: string; description: string }[] = [
  { value: 'didactic', icon: '📢', description: '单向讲授' },
  { value: 'heuristic', icon: '💡', description: '讲授+提问' },
  { value: 'discussion', icon: '💬', description: '频繁互动' },
]

const MODE_COLORS: Record<TeachingMode, { bg: string; border: string }> = {
  didactic: { bg: '#FFF3E0', border: '#FB8500' },
  heuristic: { bg: '#F3E5F5', border: '#9D4EDD' },
  discussion: { bg: '#FCE4EC', border: '#E63946' },
}

export default function ObservationConfig() {
  const navigate = useNavigate()

  const [topic, setTopic] = useState('')
  const [teachingMode, setTeachingMode] = useState<TeachingMode>('heuristic')
  const [students, setStudents] = useState<StudentProfile[]>([])
  const [studentName, setStudentName] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  const handleAddStudent = () => {
    const trimmed = studentName.trim()
    if (!trimmed) return
    const newStudent: StudentProfile = {
      name: trimmed,
      level: 'average' as StudentLevel,
      attitude: 'neutral' as StudentAttitude,
      learning_ability: 5,
    }
    setStudents((prev) => [...prev, newStudent])
    setStudentName('')
    setErrors((prev) => {
      const next = { ...prev }
      delete next.students
      return next
    })
  }

  const handleRemoveStudent = (index: number) => {
    setStudents((prev) => prev.filter((_, i) => i !== index))
  }

  const handleStudentNameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddStudent()
    }
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    if (!topic.trim()) {
      newErrors.topic = '请输入教学主题'
    }
    if (students.length === 0) {
      newErrors.students = '请至少添加一名学生'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return

    setSubmitting(true)
    try {
      const response = await startObservation({
        topic: topic.trim(),
        teaching_mode: teachingMode,
        checkpoint_count: 5,
        students,
      })
      navigate(`/observation/session/${response.session_id}`)
    } catch (err) {
      setErrors({ submit: err instanceof Error ? err.message : '启动失败' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Wrapper>
      {/* 导航栏 */}
      <PageNav title="观察模式 - 配置" onBack={() => navigate('/')} />

      <main className="config-main">
        {/* 步骤 1：教学主题 */}
        <section className="step-card">
          <h2 className="step-title">步骤 1：教学主题</h2>
          <p className="step-desc">请输入本次教学的主题内容</p>
          <RoughInput
            placeholder="例如：Python变量与数据类型"
            value={topic}
            onChange={(e) => {
              setTopic(e.target.value)
              if (errors.topic) setErrors((prev) => ({ ...prev, topic: '' }))
            }}
          />
          {errors.topic && <p className="error-text">{errors.topic}</p>}
        </section>

        {/* 步骤 2：教学模式 */}
        <section className="step-card">
          <h2 className="step-title">步骤 2：选择教学模式</h2>
          <div className="mode-buttons">
            {TEACHING_MODES.map((mode) => {
              const colors = MODE_COLORS[mode.value]
              const isSelected = teachingMode === mode.value
              return (
                <button
                  key={mode.value}
                  className={`mode-btn ${isSelected ? 'selected' : ''}`}
                  style={{
                    background: colors.bg,
                    borderColor: isSelected ? colors.border : '#1A1A1A',
                    boxShadow: isSelected ? `4px 4px 0px ${colors.border}` : '3px 3px 0px rgba(0,0,0,0.2)',
                  }}
                  onClick={() => setTeachingMode(mode.value)}
                >
                  <span className="mode-icon">{mode.icon}</span>
                  <span className="mode-name">{TEACHING_MODE_LABELS[mode.value]}</span>
                  <span className="mode-desc">{mode.description}</span>
                </button>
              )
            })}
          </div>
        </section>

        {/* 步骤 3：学生配置 */}
        <section className="step-card">
          <h2 className="step-title">步骤 3：学生配置</h2>

          <div className="student-add-row">
            <RoughInput
              placeholder="学生姓名"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              onKeyDown={handleStudentNameKeyDown}
            />
            <RoughButton variant="outline" onClick={handleAddStudent}>
              + 添加学生
            </RoughButton>
          </div>

          {errors.students && <p className="error-text">{errors.students}</p>}

          {students.length > 0 && (
            <div className="student-list">
              {students.map((student, index) => (
                <StudentChip
                  key={student.name}
                  name={student.name}
                  level={student.level}
                  onDelete={() => handleRemoveStudent(index)}
                />
              ))}
            </div>
          )}
        </section>

        {/* 提交错误 */}
        {errors.submit && <p className="error-text error-submit">{errors.submit}</p>}

        {/* 开始观察按钮 */}
        <div className="submit-area">
          <RoughButton
            variant="primary"
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? '正在启动...' : '开始观察 →'}
          </RoughButton>
        </div>
      </main>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  background: #fafafa;
  color: #1a1a1a;
  font-family: 'Be Vietnam Pro', system-ui, sans-serif;

  /* ===== 主内容 ===== */
  .config-main {
    max-width: 800px;
    margin: 0 auto;
    padding: 32px 24px 80px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  /* ===== 步骤卡片 ===== */
  .step-card {
    background: #fff9c4;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 24px;
    transform: rotate(-0.3deg);
  }

  .step-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 8px;
    padding-bottom: 8px;
    border-bottom: 2px solid #1a1a1a;
  }

  .step-desc {
    font-size: 14px;
    color: #6c757d;
    margin-bottom: 16px;
  }

  /* ===== 教学模式按钮 ===== */
  .mode-buttons {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
  }

  .mode-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    width: 120px;
    padding: 16px 12px;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      transform: translate(-2px, -2px);
    }

    &.selected {
      border-width: 3px;
    }
  }

  .mode-icon {
    font-size: 28px;
  }

  .mode-name {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 16px;
    font-weight: 700;
  }

  .mode-desc {
    font-size: 12px;
    color: #6c757d;
  }

  /* ===== 学生配置 ===== */
  .student-add-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }

  .student-add-row > *:first-child {
    flex: 1;
  }

  .student-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
  }

  /* ===== 错误提示 ===== */
  .error-text {
    color: #e63946;
    font-size: 14px;
    font-weight: 600;
    margin-top: 8px;
  }

  .error-submit {
    text-align: center;
  }

  /* ===== 提交区域 ===== */
  .submit-area {
    display: flex;
    justify-content: center;
    padding-top: 16px;
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/views/ObservationConfig.test.tsx
```

**预期结果：** 12 个测试全部通过。

- [ ] **步骤 5：提交**

```bash
git add frontend/src/views/ObservationConfig.tsx frontend/tests/views/ObservationConfig.test.tsx
git commit -m "feat(observation-frontend): 实现 ObservationConfig 配置页面（主题+模式+学生+提交）"
```

---

## 任务 6：实现 ObservationView 视图（实时观察页面）

目标：实现观察模式实时观察页面，显示 WebSocket 消息流、检查点进度、教学模式徽章和已进行时间。页面为只读模式，用户无法干预 agent 行为。

**相关文件：**
- 新建：`frontend/src/views/ObservationView.tsx`
- 新建：`frontend/tests/views/ObservationView.test.tsx`

### 任务 6.1：编写 ObservationView 失败测试（RED）

- [ ] **步骤 1：创建 ObservationView 测试**

新建 `frontend/tests/views/ObservationView.test.tsx`：

```typescript
// frontend/tests/views/ObservationView.test.tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import ObservationView from '../../src/views/ObservationView'
import type { WsMessageEvent } from '../../src/types/observation'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ sessionId: '42' }),
  }
})

// useWebSocket mock 默认返回值
const defaultMockWsReturn = {
  connectionState: 'connected' as const,
  messages: [] as WsMessageEvent[],
  checkpointState: null,
  sessionEnded: false,
  teachingMode: 'heuristic' as const,
}

vi.mock('../../src/hooks/useWebSocket', () => ({
  useWebSocket: () => defaultMockWsReturn,
}))

// 同时 mock useWebSocketBase（TeacherView 可能直接使用）
vi.mock('../../src/hooks/useWebSocketBase', () => ({
  useWebSocketBase: () => defaultMockWsReturn,
}))

// useElapsedTime mock
vi.mock('../../src/hooks/useElapsedTime', () => ({
  useElapsedTime: () => '00:00',
}))

beforeEach(() => {
  mockNavigate.mockClear()
  // 重置 mock 返回值
  defaultMockWsReturn.connectionState = 'connected'
  defaultMockWsReturn.messages = []
  defaultMockWsReturn.checkpointState = null
  defaultMockWsReturn.sessionEnded = false
})

function renderView() {
  return render(
    <MemoryRouter>
      <ObservationView />
    </MemoryRouter>,
  )
}

describe('ObservationView', () => {
  it('renders page title with session ID', () => {
    renderView()
    expect(screen.getByRole('heading', { name: /观察模式 - 实时观察/ })).toBeInTheDocument()
  })

  it('renders back button', () => {
    renderView()
    expect(screen.getByRole('button', { name: '← 返回' })).toBeInTheDocument()
  })

  it('navigates to home on back button click', async () => {
    const user = userEvent.setup()
    renderView()
    await user.click(screen.getByRole('button', { name: '← 返回' }))
    expect(mockNavigate).toHaveBeenCalledWith('/')
  })

  it('shows elapsed time display', () => {
    renderView()
    expect(screen.getByText('已进行')).toBeInTheDocument()
    expect(screen.getByText('00:00')).toBeInTheDocument()
  })

  it('shows message count as 0 when no messages', () => {
    renderView()
    expect(screen.getByText('消息：0')).toBeInTheDocument()
  })

  it('renders teacher lecture message with correct style', () => {
    defaultMockWsReturn.messages = [
      {
        type: 'message',
        session_id: 42,
        sender: 'teacher',
        message_type: 'lecture',
        content: '今天我们学习Python变量与数据类型。',
      },
    ]
    renderView()

    expect(screen.getByText('今天我们学习Python变量与数据类型。')).toBeInTheDocument()
    expect(screen.getByText('教师')).toBeInTheDocument()
  })

  it('renders student answer message with name', () => {
    defaultMockWsReturn.messages = [
      {
        type: 'message',
        session_id: 42,
        sender: '张三',
        message_type: 'answer_to_checkpoint',
        content: '变量名必须以字母或下划线开头。',
      },
    ]
    renderView()

    expect(screen.getByText('变量名必须以字母或下划线开头。')).toBeInTheDocument()
    expect(screen.getByText('张三')).toBeInTheDocument()
  })

  it('renders checkpoint question message', () => {
    defaultMockWsReturn.messages = [
      {
        type: 'message',
        session_id: 42,
        sender: 'teacher',
        message_type: 'checkpoint_question',
        content: '变量的命名规则是什么？',
      },
    ]
    renderView()

    expect(screen.getByText('变量的命名规则是什么？')).toBeInTheDocument()
    expect(screen.getByText('检查点问题')).toBeInTheDocument()
  })

  it('shows connecting state', () => {
    defaultMockWsReturn.connectionState = 'connecting'
    renderView()
    expect(screen.getByText('连接中...')).toBeInTheDocument()
  })

  it('shows disconnected state', () => {
    defaultMockWsReturn.connectionState = 'disconnected'
    renderView()
    expect(screen.getByText('连接已断开')).toBeInTheDocument()
  })

  it('renders checkpoint progress sidebar when checkpointState is set', () => {
    defaultMockWsReturn.checkpointState = {
      index: 0,
      checkpoint: { title: 'Python简介', state: 'teaching', key_point: '基础语法' },
      progress: { current: 1, total: 5, completed: 0 },
    }
    renderView()

    expect(screen.getByText('检查点进度')).toBeInTheDocument()
    expect(screen.getByText('Python简介')).toBeInTheDocument()
    expect(screen.getByText('1 / 5')).toBeInTheDocument()
  })

  it('shows session ended message when sessionEnded is true', () => {
    defaultMockWsReturn.sessionEnded = true
    renderView()
    expect(screen.getByText('会话已结束')).toBeInTheDocument()
  })

  it('updates message count when messages arrive', () => {
    defaultMockWsReturn.messages = [
      { type: 'message', session_id: 42, sender: 'teacher', message_type: 'lecture', content: 'A' },
      { type: 'message', session_id: 42, sender: '张三', message_type: 'answer_to_checkpoint', content: 'B' },
      { type: 'message', session_id: 42, sender: 'teacher', message_type: 'reply_to_student', content: 'C' },
    ]
    renderView()
    expect(screen.getByText('消息：3')).toBeInTheDocument()
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/views/ObservationView.test.tsx
```

### 任务 6.2：实现 ObservationView 视图（GREEN）

- [ ] **步骤 3：创建 `frontend/src/views/ObservationView.tsx`**

新建 `frontend/src/views/ObservationView.tsx`：

```tsx
// frontend/src/views/ObservationView.tsx
import { useMemo } from 'react'
import styled from 'styled-components'
import { useNavigate, useParams } from 'react-router-dom'
import RoughButton from '../components/RoughButton'
import RoughBadge from '../components/RoughBadge'
import { useWebSocket } from '../hooks/useWebSocket'
import { useElapsedTime } from '../hooks/useElapsedTime'
import { TEACHING_MODE_LABELS } from '../types/observation'
import type { WsMessageEvent, CheckpointState } from '../types/observation'

/** 根据消息类型返回便签背景色 */
function getMessageStyle(messageType: string): { bg: string; border: string; label: string } {
  switch (messageType) {
    case 'lecture':
      return { bg: '#E3F2FD', border: '#2E5CFF', label: '教师' }
    case 'checkpoint_question':
      return { bg: '#F3E5F5', border: '#9D4EDD', label: '检查点问题' }
    case 'answer_to_checkpoint':
      return { bg: '#FFF9C4', border: '#1A1A1A', label: '学生回答' }
    case 'reply_to_student':
      return { bg: '#E3F2FD', border: '#2E5CFF', label: '教师回复' }
    case 'question_to_teacher':
      return { bg: '#FFF3E0', border: '#FB8500', label: '学生提问' }
    case 'assign_homework':
      return { bg: '#E8F5E9', border: '#06D6A0', label: '布置作业' }
    case 'homework_submission':
      return { bg: '#E8F5E9', border: '#06D6A0', label: '提交作业' }
    case 'homework_feedback':
      return { bg: '#E8F5E9', border: '#06D6A0', label: '作业反馈' }
    case 'feedback_submission':
      return { bg: '#FCE4EC', border: '#E63946', label: '课程反馈' }
    case 'end_feedback':
      return { bg: '#FCE4EC', border: '#E63946', label: '课程结束' }
    default:
      return { bg: '#FFFFFF', border: '#1A1A1A', label: '消息' }
  }
}

/** 根据检查点状态返回颜色 */
function getCheckpointStateColor(state: CheckpointState): string {
  switch (state) {
    case 'pending': return '#FFE0B2'
    case 'teaching': return '#BBDEFB'
    case 'questions': return '#E1BEE7'
    case 'complete': return '#C8E6C9'
    default: return '#F0F0F0'
  }
}

/** 根据检查点状态返回图标 */
function getCheckpointStateIcon(state: CheckpointState): string {
  switch (state) {
    case 'pending': return '⏳'
    case 'teaching': return '🔄'
    case 'questions': return '❓'
    case 'complete': return '✅'
    default: return '⏳'
  }
}

export default function ObservationView() {
  const navigate = useNavigate()
  const { sessionId } = useParams<{ sessionId: string }>()
  const numericSessionId = Number(sessionId) || 0

  const { connectionState, messages, checkpointState, sessionEnded, teachingMode } = useWebSocket(numericSessionId)
  const elapsedTime = useElapsedTime(connectionState === 'connected')

  // 生成检查点列表（基于当前进度）
  const checkpoints = useMemo(() => {
    if (!checkpointState) return []
    const { progress, index, checkpoint } = checkpointState
    const items: { title: string; state: CheckpointState; isCurrent: boolean }[] = []
    for (let i = 0; i < progress.total; i++) {
      if (i < progress.completed) {
        items.push({ title: `检查点 ${i + 1}`, state: 'complete', isCurrent: false })
      } else if (i === index) {
        items.push({ title: checkpoint.title, state: checkpoint.state as CheckpointState, isCurrent: true })
      } else {
        items.push({ title: `检查点 ${i + 1}`, state: 'pending', isCurrent: false })
      }
    }
    return items
  }, [checkpointState])

  // teachingMode 从 WebSocket session_state 事件获取，初始为 null 时显示模式名称
  const teachingModeDisplay = teachingMode ? TEACHING_MODE_LABELS[teachingMode] ?? teachingMode : ''

  return (
    <Wrapper>
      {/* 顶部状态栏 */}
      <PageNav
        title="观察模式 - 实时观察"
        onBack={() => navigate('/')}
        right={
          <>
            {teachingModeDisplay && <RoughBadge variant="blue" rotation={-1}>{teachingModeDisplay}</RoughBadge>}
            {checkpointState && (
              <RoughBadge variant="yellow" rotation={2}>
                检查点 {checkpointState.progress.current}/{checkpointState.progress.total}
              </RoughBadge>
            )}
            <span className="elapsed-label">已进行</span>
            <span className="elapsed-time">{elapsedTime}</span>
            <span className="message-count">消息：{messages.length}</span>
          </>
        }
      />

      {/* 主内容区 */}
      <div className="content-layout">
        {/* 消息流 */}
        <main className="message-area">
          {connectionState === 'connecting' && (
            <div className="status-message">连接中...</div>
          )}
          {connectionState === 'disconnected' && (
            <div className="status-message error">连接已断开</div>
          )}
          {sessionEnded && (
            <div className="session-ended-banner">会话已结束</div>
          )}

          {messages.map((msg, index) => (
            <MessageBubble
              key={`${msg.sender}-${msg.message_type}-${index}`}
              message={msg}
            />
          ))}

          {messages.length === 0 && connectionState === 'connected' && (
            <div className="status-message">等待教学开始...</div>
          )}
        </main>

        {/* 右侧边栏 */}
        {checkpoints.length > 0 && (
          <aside className="sidebar">
            <div className="sidebar-card">
              <h3 className="sidebar-title">检查点进度</h3>
              <div className="checkpoint-list">
                {checkpoints.map((cp, i) => (
                  <div
                    key={i}
                    className={`checkpoint-item ${cp.isCurrent ? 'current' : ''}`}
                    style={{ background: getCheckpointStateColor(cp.state) }}
                  >
                    <span className="checkpoint-icon">{getCheckpointStateIcon(cp.state)}</span>
                    <span className="checkpoint-title">{cp.title}</span>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        )}
      </div>
    </Wrapper>
  )
}

/** 消息气泡组件（内部组件） */
function MessageBubble({ message }: { message: WsMessageEvent }) {
  const style = getMessageStyle(message.message_type)
  const isTeacher = message.sender === 'teacher'

  return (
    <div
      className="message-bubble"
      style={{ background: style.bg, borderColor: style.border }}
    >
      <div className="message-header">
        <span className="message-sender">
          {isTeacher ? '👨‍🏫' : '👤'} {isTeacher ? style.label : message.sender}
        </span>
        {!isTeacher && (
          <RoughBadge variant="yellow" rotation={1}>{style.label}</RoughBadge>
        )}
      </div>
      <p className="message-content">{message.content}</p>
    </div>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  background: #fafafa;
  color: #1a1a1a;
  font-family: 'Be Vietnam Pro', system-ui, sans-serif;
  display: flex;
  flex-direction: column;

  .elapsed-label {
    font-size: 14px;
    color: #6c757d;
  }

  .elapsed-time {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #1a1a1a;
    font-variant-numeric: tabular-nums;
  }

  .message-count {
    font-size: 14px;
    color: #6c757d;
    font-weight: 600;
  }

  /* ===== 内容布局 ===== */
  .content-layout {
    display: flex;
    flex: 1;
    gap: 24px;
    padding: 24px;
    max-width: 1280px;
    margin: 0 auto;
    width: 100%;
  }

  /* ===== 消息流 ===== */
  .message-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: calc(100dvh - 80px);
    overflow-y: auto;
    padding-right: 8px;
  }

  .status-message {
    text-align: center;
    padding: 32px;
    color: #6c757d;
    font-size: 16px;
    font-style: italic;

    &.error {
      color: #e63946;
    }
  }

  .session-ended-banner {
    text-align: center;
    padding: 16px;
    background: #fce4ec;
    border: 2px solid #e63946;
    border-radius: 8px;
    font-weight: 700;
    color: #e63946;
    box-shadow: 3px 3px 0px 0px #1a1a1a;
  }

  /* ===== 消息气泡 ===== */
  .message-bubble {
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 2px 2px 0px 0px #1a1a1a;
  }

  .message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .message-sender {
    font-weight: 700;
    font-size: 14px;
  }

  .message-content {
    font-size: 15px;
    line-height: 1.6;
    margin: 0;
    white-space: pre-wrap;
  }

  /* ===== 右侧边栏 ===== */
  .sidebar {
    width: 280px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .sidebar-card {
    background: #ffffff;
    border: 2px solid #6c757d;
    border-radius: 8px;
    padding: 16px;
  }

  .sidebar-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #d4d4d4;
  }

  .checkpoint-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .checkpoint-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 14px;
    border: 1px solid transparent;

    &.current {
      border-color: #1a1a1a;
      font-weight: 700;
      box-shadow: 2px 2px 0px 0px #1a1a1a;
    }
  }

  .checkpoint-icon {
    font-size: 16px;
    flex-shrink: 0;
  }

  .checkpoint-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* ===== 响应式 ===== */
  @media (max-width: 768px) {
    .content-layout {
      flex-direction: column;
      padding: 16px;
    }

    .sidebar {
      width: 100%;
    }

    .status-bar {
      flex-wrap: wrap;
      gap: 8px;
    }

    .status-badges {
      margin-left: 0;
      width: 100%;
      justify-content: flex-start;
    }
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/views/ObservationView.test.tsx
```

**预期结果：** 14 个测试全部通过。

- [ ] **步骤 5：提交**

```bash
git add frontend/src/views/ObservationView.tsx frontend/tests/views/ObservationView.test.tsx
git commit -m "feat(observation-frontend): 实现 ObservationView 实时观察页面（消息流+检查点进度+状态栏）"
```

---

## 任务 7：配置路由（App.tsx）

目标：在 `App.tsx` 中添加观察模式的两个路由，将 URL 与视图组件关联。

**相关文件：**
- 修改：`frontend/src/App.tsx`

### 任务 7.1：修改 App.tsx 添加路由

- [ ] **步骤 1：修改 `frontend/src/App.tsx`，添加观察模式路由**

更新 `frontend/src/App.tsx`：

```tsx
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'
import ObservationConfig from './views/ObservationConfig'
import ObservationView from './views/ObservationView'
import NotFoundPage from './views/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/observation/config" element={<ObservationConfig />} />
      <Route path="/observation/session/:sessionId" element={<ObservationView />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
```

- [ ] **步骤 2：运行全部测试，确认通过**

```bash
cd frontend
npm run test
```

**预期结果：** 所有测试通过（包括 App 级别和 LandingPage 的已有测试）。

- [ ] **步骤 3：提交**

```bash
git add frontend/src/App.tsx
git commit -m "feat(observation-frontend): 配置观察模式路由（/observation/config 和 /observation/session/:sessionId）"
```

---

## 任务 8：ESLint 检查与最终验证

目标：确保所有新增代码通过 ESLint 检查，全部测试通过。

### 任务 8.1：运行 ESLint 和测试

- [ ] **步骤 1：运行 ESLint**

```bash
cd frontend
npm run lint
```

**预期结果：** 无错误。如有 lint 错误，修复后重新运行。

- [ ] **步骤 2：运行全部测试**

```bash
cd frontend
npm run test
```

**预期结果：** 所有测试通过（预期新增 51 个测试：类型 9 + API 4 + WebSocket 7 + 计时器 5 + Config 12 + View 14，加上已有约 73 个测试，总计约 124 个测试）。

- [ ] **步骤 3：如有修复，提交**

```bash
git add -A
git commit -m "chore(observation-frontend): 修复 lint 和测试问题"
```

---

## 功能完成前的最终检查清单

在宣告「Phase 10: 观察模式前端（核心UI）开发完成」之前，请确保：

- [ ] `npm run test` 全部通过（预期 51+ 个测试）
- [ ] `npm run lint` 无错误
- [ ] `npm run build` 构建成功
- [ ] `/observation/config` 页面正确渲染，包含教学主题输入、教学模式选择、学生配置和开始按钮
- [ ] 教学模式默认选中"启发式"，可切换
- [ ] 学生可通过姓名手动添加和删除
- [ ] 表单验证正确（空主题、无学生时显示错误提示）
- [ ] 点击"开始观察"调用 `POST /observation/start` 并跳转到 `/observation/session/:sessionId`
- [ ] `/observation/session/:sessionId` 页面正确渲染，显示顶部状态栏和消息流区域
- [ ] WebSocket hook 正确连接、接收消息、分发到状态
- [ ] 检查点状态变更时右侧边栏更新进度列表
- [ ] 已进行时间实时更新（每秒）
- [ ] 消息根据类型显示不同背景色（教师蓝色、学生黄色、问题紫色等）
- [ ] 连接状态正确显示（连接中/已断开）
- [ ] 会话结束时显示结束提示
- [ ] 所有 UI 组件遵循 rough-design 手绘草图风格
- [ ] 每个组件文件只有一个 `Wrapper` styled component
- [ ] 内部元素使用 `className`（kebab-case）+ 多层嵌套选择器
- [ ] 测试文件位于 `tests/` 目录（不与源文件 co-locate）
- [ ] 测试导入使用相对路径（`../../src/...`）
