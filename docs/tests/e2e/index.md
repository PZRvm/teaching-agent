# E2E (端到端) 测试文档

本文档描述端到端测试体系。

## 测试框架

| 框架 | 用途 | 状态 |
|------|------|------|
| Playwright | 跨浏览器 E2E 测试 | 可选 |
| Vitest + Testing Library | 集成测试（轻量级） | 推荐 |

## 测试文件结构

```
e2e/
├── observation.spec.ts    # 观察模式 E2E 测试
├── teacher.spec.ts        # 教师模式 E2E 测试
└── auth.spec.ts           # 认证流程测试（未来）
```

---

## 测试场景

### 观察模式完整流程

1. 访问首页
2. 点击"观察模式"
3. 填写教学主题：`"Python 基础"`
4. 选择教学模式：`"灌输式"`
5. 配置学生：选择随机生成，30 人
6. 点击"开始观察"
7. 验证 WebSocket 连接建立
8. 验证实时消息显示
9. 等待会话结束
10. 验证跳转到报告页面
11. 验证报告包含量化指标

### 教师模式完整流程

1. 访问首页
2. 点击"教师模式"
3. 配置教学会话
4. 点击"开始教学"
5. 教师输入讲授内容
6. 验证学生响应显示
7. 布置作业
8. 验证作业提交
9. 查看反馈

---

## 使用 Playwright（可选）

### 安装

```bash
npm install -D @playwright/test
npx playwright install
```

### 测试示例

```typescript
// e2e/observation.spec.ts
import { test, expect } from '@playwright/test'

test.describe('观察模式', () => {
  test('完整流程', async ({ page }) => {
    // 1. 访问首页
    await page.goto('http://localhost:5173')
    
    // 2. 点击观察模式
    await page.click('text=观察模式')
    
    // 3. 填写配置
    await page.fill('[name="topic"]', 'Python 基础')
    await page.selectOption('[name="teachingMode"]', 'didactic')
    await page.click('text=随机生成')
    await page.fill('[name="totalStudents"]', '30')
    
    // 4. 开始观察
    await page.click('text=开始观察')
    
    // 5. 验证跳转到观察视图
    await expect(page).toHaveURL(/\/observation\/view\/\d+/)
    
    // 6. 验证消息显示
    await expect(page.locator('.message-list')).toBeVisible()
    
    // 7. 等待会话结束（最多 5 分钟）
    await page.waitForURL(/\/observation\/report\/\d+/, { timeout: 300000 })
    
    // 8. 验证报告
    await expect(page.locator('text=参与率')).toBeVisible()
    await expect(page.locator('text=正确率')).toBeVisible()
  })
})
```

### 运行 Playwright 测试

```bash
# 运行所有 E2E 测试
npx playwright test

# 运行特定测试
npx playwright test e2e/observation.spec.ts

# 显示浏览器运行
npx playwright test --headed

# 生成测试报告
npx playwright show-report

# 调试模式
npx playwright test --debug
```

---

## 使用 Vitest 集成测试（推荐）

对于不需要真实浏览器的集成测试，可以使用 vitest + Testing Library。

### 测试示例

```typescript
// e2e/observation-flow.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import App from '../src/App'

const server = setupServer(
  http.post('/api/observation/start', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      session_id: 'test-123',
      status: 'running',
      ...body,
    })
  }),
  http.ws('/api/ws/test-123', async ({ client }) => {
    // 模拟 WebSocket 消息
    client.send(JSON.stringify({
      sender: 'teacher',
      message_type: 'lecture',
      content: 'Welcome to the class',
    }))
  })
)

describe('观察模式流程', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('完整流程：配置到报告', async () => {
    render(<App />)
    
    const user = userEvent.setup()
    
    // 点击观察模式
    await user.click(screen.getByText('观察模式'))
    
    // 配置会话
    await user.type(screen.getByLabelText('教学主题'), 'Python 基础')
    await user.selectOptions(screen.getByLabelText('教学模式'), 'didactic')
    
    // 开始观察
    await user.click(screen.getByText('开始观察'))
    
    // 验证跳转
    await waitFor(() => {
      expect(screen.getByText(/观察中/)).toBeInTheDocument()
    })
  })
})
```

### 运行集成测试

```bash
# 在前端目录
npm test -- e2e/
```

---

## 测试数据准备

### 使用 Fixtures

```typescript
// e2e/fixtures.ts
export const mockTeachingSession = {
  teaching_mode: 'didactic',
  topic: 'Python 基础',
  students_config: {
    source: 'random',
    random_config: {
      total_students: 30,
    },
  },
}

export const mockMessages = [
  {
    sender: 'teacher',
    message_type: 'lecture',
    content: 'Welcome to the class',
  },
  {
    sender: 'Alice',
    message_type: 'answer_to_checkpoint',
    content: 'I understand',
  },
]
```

---

## 测试环境配置

### 前端开发服务器

测试时需要前端开发服务器运行：

```bash
cd frontend
npm run dev
# 运行在 http://localhost:5173
```

### 后端 API 服务器

测试时需要后端 API 服务器运行：

```bash
cd backend
python main.py
# 运行在 http://localhost:8000
```

### 环境变量

创建 `.env.test` 文件：

```bash
# frontend/.env.test
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    
    services:
      frontend:
        image: node:20
        options: --cwd frontend
        run: |
          npm install
          npm run build
          npm run preview --host localhost --port 5173 &
      
      backend:
        image: python:3.12
        options: --cwd backend
        run: |
          pip install -r requirements.txt
          python main.py &
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Playwright
        run: npm install -D @playwright/test
      
      - name: Install browsers
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npx playwright test
```

---

## 常见问题

### Q: WebSocket 连接在测试中失败？

**原因**: 测试环境无法建立真实的 WebSocket 连接。

**解决方案**:
1. 使用 MSW mock WebSocket：`http.ws('/api/ws/:id', ...)`
2. 使用 fake-websocket 库
3. 提取 WebSocket hook 为可测试的接口

### Q: 测试超时？

**原因**: 默认超时时间太短。

**解决方案**:
```typescript
test('slow test', async ({ page }) => {
  test.setTimeout(60000) // 60 秒超时
  // ...
})
```

### Q: 选择器不稳定？

**原则**: 优先使用可访问性选择器。

```typescript
// ✅ 好的选择器
page.getByRole('button', { name: '开始观察' })
page.getByLabelText('教学主题')
page.getByText('观察模式')

// ❌ 避免的选择器
page.locator('div.container > button:nth-child(2)')
page.locator('[class*="start-button"]')
```

### Q: 测试在 CI 中失败但在本地通过？

**原因**: 环境差异（网络速度、时区、字体等）

**解决方案**:
1. 使用 `waitFor` 替代固定延迟
2. 设置合理的超时时间
3. 确保测试环境一致
4. 使用 CI 专用的测试账号和数据
