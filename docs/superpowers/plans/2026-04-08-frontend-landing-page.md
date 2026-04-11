# 前端首页（Landing Page）实现计划

> **给 agentic 工作者：** REQUIRED SUB-SKILL：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐条执行本计划。步骤使用复选框（`- [ ]`）语法方便跟踪。

**Goal：** 实现教学智能体系统的前端主首页（模式选择页），用于在进入系统时选择「观察模式 / 教师模式」，整体视觉采用 `rough-design`（手绘草图风格），布局严格参考 `docs/frontend-design-prompts/demo.html`，并引入 `react-router-dom` 作为前端路由系统。

**Architecture：** 使用 `App.tsx` 作为路由容器，`main.tsx` 中包裹 `BrowserRouter`。页面组件统一放在 `src/views/` 目录，本首页实现为 `LandingPage` 视图；全局可复用的粗风格按钮封装为 `RoughButton` 组件，放在 `src/components/`，其它页面共用。所有样式统一使用 `styled-components`，每个组件文件只保留一个 `Wrapper`，所有内部结构通过 `className` + 多层嵌套选择器实现（不再创建额外的 styled 组件），并按照 rough-design 约定实现粗边框、硬阴影、胶带、便签色、轻微旋转等视觉效果。

**Tech Stack：** React + TypeScript + Vite，styled-components，react-router-dom，Vitest + React Testing Library。

---

## 文件结构（File Structure）

本计划会创建/修改的文件如下：

- **已存在（Existing）**
  - `frontend/src/App.tsx` —— 修改为路由容器，使用 `<Routes>` / `<Route>` 渲染首页。
  - `frontend/src/main.tsx` —— 在入口中引入 `BrowserRouter` 包裹 `<App />`。
  - `frontend/src/index.css` —— 如有需要，可在后续计划中调整全局字体/背景以更贴近 rough-design（本计划先不动）。

- **新增（New）**
  - `frontend/src/views/LandingPage.tsx` —— 首页视图组件，实现 demo.html 描述的布局和 rough-design 风格。
  - `frontend/src/views/LandingPage.test.tsx` —— 使用 Vitest + React Testing Library 的首页组件测试（渲染 + 结构性检查 + 导航意图）。
  - `frontend/src/components/RoughButton.tsx` —— 全局粗风格按钮组件，封装 rough-design 按钮视觉，供 LandingPage 和其他页面复用。
  - `frontend/src/components/RoughButton.test.tsx` —— 按钮组件的单元测试（渲染 + 点击回调）。
  - `frontend/src/App.test.tsx` —— App 级别测试，验证在 `/` 路由下渲染 LandingPage 的关键内容。

路由系统下的 `/observation/config`、`/teacher/config`、`/history` 等页面会在其它计划中实现，本计划只负责：

- 引入 `react-router-dom` 并配置基础路由结构
- 首页本身的布局、样式和按钮导航意图（通过 `useNavigate`）

---

## 本计划共用的 rough-design 视觉约定

以下约定统一应用于首页实现，**严格参考 `demo.html` 的实际渲染效果**：

### 颜色（Colors）—— 严格对齐 demo.html tailwind config

- 页面背景：`#f9f9f9`（`bg-surface`）
- 文字主色：`#1a1c1c`（`text-on-surface`）
- 文字副色：`#747688`（`text-outline`）
- 观察模式卡片背景：`#E3F2FD`（`bg-sticky-blue`）
- 观察模式卡片边框：`#2e5cff`（`border-primary`）
- 观察模式按钮背景：`#2e5cff`（`bg-primary`），hover：`#2e5cff`（`bg-primary-container`）
- 教师模式卡片背景：`#E8F5E9`（`bg-sticky-green`）
- 教师模式卡片边框：`#007d5c`（`border-tertiary-container`）
- 教师模式按钮背景：`#007d5c`（`bg-tertiary-container`），hover：`#006247`（`bg-tertiary`）
- 便签粉色：`#FCE4EC`（`bg-sticky-pink`）
- 便签黄色：`#FFF9C4`（`bg-sticky-yellow`）
- 阴影/边框主色：`#1A1A1A`

### 边框与阴影（Borders & Shadows）

- 导航栏：`border-bottom: 2px solid #1a1a1a`（实线，非虚线）+ `box-shadow: 4px 4px 0px 0px #1A1A1A`
- 卡片边框：`3px solid`（观察模式 `#2e5cff`，教师模式 `#007d5c`）—— 注意：不是统一黑色
- 默认阴影：`box-shadow: 4px 4px 0px 0px #1A1A1A`
- 悬停阴影：`box-shadow: 8px 8px 0px 0px #1A1A1A`
- 按钮：`border: 2px solid #1a1a1a` + `box-shadow: 4px 4px 0px 0px #1A1A1A`

### 不完美感（Imperfection）

- 观察模式卡片旋转：`transform: rotate(-0.5deg)`
- 教师模式卡片旋转：`transform: rotate(1deg)`（demo.html 是 1deg 不是 0.5deg）
- 卡片 hover 位移：`transform: translate(-4px, -4px)`（demo.html 是 `-translate-x-1 -translate-y-1`，即 4px）

### 胶带装饰（Tape Decorations）

- 使用 `background: rgba(227, 242, 253, 0.6)` + `backdrop-filter: blur(1px)` + `border-x: 1px solid rgba(200, 200, 200, 0.3)`
- 观察模式胶带：`position: absolute; top: -16px; left: -8px; rotate(-15deg); width: 64px; height: 32px`
- 教师模式胶带：`position: absolute; top: -16px; right: -8px; rotate(15deg); width: 64px; height: 32px`

### 字体（Typography）

- 标题：`font-family: 'Plus Jakarta Sans', sans-serif`
- 正文：`font-family: 'Be Vietnam Pro', sans-serif`
- 导航栏品牌名 "SimuSketch"：`font-family: 'Plus Jakarta Sans'; font-weight: 900; font-size: 24px; text-decoration: underline wavy blue-500`

### 导航栏布局（严格对齐 demo.html）

- 背景：`#fafafa`（`bg-slate-50`）或 `rgba(250, 250, 250, 0.95)`
- 左侧：`SimuSketch`（粗体、wavy underline 蓝色下划线）+ 竖线分隔符（`rotate(12deg); 2px宽; 24px高`）+ `教学智能体`（粗体 18px）
- 右侧：Material Icons `history` 按钮 + `settings` 按钮 + 圆形头像（带 sketch-shadow）
- **注意**：demo.html 右侧不是文字按钮，而是 Material Symbols Outlined 图标按钮

### 主标题区装饰（demo.html 独有）

- h1 下方：SVG 手绘波浪线 `<path d="M0 10 Q 25 0, 50 10 T 100 10" stroke="currentColor" stroke-width="4" fill="transparent" stroke-linecap="round">`，颜色 `#2e5cff`（primary）
- 副标题下方：SVG 虚线 `<path d="M0 5 L 100 5" stroke="currentColor" stroke-dasharray="5 5" stroke-width="2">`，颜色 `#b7102a`（secondary），宽度 192px

### 卡片描述文案（使用 demo.html 原文）

- 观察模式：`进入旁观席位，观察多个AI智能体在模拟课堂中的实时互动、逻辑推演与反馈循环。深入剖析Agent间的协同机制与知识传递路径。`
- 教师模式：`扮演引导者角色，直接参与教学模拟。设定教学目标，干预Agent学习进程，并在高保真模拟环境中验证您的教学策略与课程设计。`

### 卡片装饰图标（demo.html 使用 Material Icons）

- 观察模式右下角：`query_stats`（Material Symbols Outlined，60px，opacity 0.1，hover 0.2）
- 教师模式右上角：`grade`（Material Symbols Outlined，filled，30px，颜色 `#27e0a9`（tertiary-fixed-dim），rotate 12deg）
- 教师模式右下角：`school`（Material Symbols Outlined，60px，opacity 0.1，hover 0.2）

### Footer 布局（严格对齐 demo.html）

- 手绘分割线：`2px height; bg-neutral-300; 带有 skewX(12deg) 的叠加效果`
- 技术栈文字：14px，颜色 `#747688`（text-outline），其中关键词用 `#1a1c1c` 加粗
- 版本标签区：两个便签风格小标签
  - `BETA v0.8.2`：`bg-sticky-pink` + `border: 1px solid #1a1a1a` + `rotate(2deg)` + `sketch-shadow`
  - `AI SIMULATION`：`bg-sticky-yellow` + `border: 1px solid #1a1a1a` + `rotate(-1deg)` + `sketch-shadow`

### 背景装饰（demo.html 固定定位）

- 左上区域：蓝色 SVG 虚线曲线（fixed, top 25%, left -48px, z-index -10, opacity 0.2）
- 右下区域：红色 SVG 虚线圆圈（fixed, bottom 25%, right -48px, z-index -10, opacity 0.2）

### 响应式断点

- `md`（768px）：卡片从两列变单列（demo.html 使用 `md:grid-cols-2`）
- 主标题在小屏：36px
- 副标题在小屏：20px

> 样式书写规则：**所有区域、元素的样式都写在 `Wrapper` 内部，通过 `.xxx { ... }` 多层嵌套完成，不新增其它 styled 组件。**

---

## 任务 0：安装依赖

目标：在前端项目中引入 `react-router-dom`，为后续路由集成做准备。

**相关文件：**
- 修改：`frontend/package.json`、`frontend/package-lock.json`（由 npm 自动更新）

- [x] **步骤 1：安装 react-router-dom**

在项目根目录执行：

```bash
cd frontend
npm install react-router-dom
```

**预期结果：** `package.json` 中多出 `react-router-dom` 依赖，安装过程无报错。

---

## 任务 1：实现 RoughButton 全局粗风格按钮组件（TDD）

目标：封装一个全局可复用的粗风格按钮组件，统一 rough-design 按钮视觉（粗边框 + 硬阴影 + 按下缩放），供首页和后续页面使用。

**相关文件：**
- 新建：`frontend/src/components/RoughButton.tsx`
- 新建：`frontend/src/components/RoughButton.test.tsx`

### 任务 1.1：为 RoughButton 编写失败测试（RED）

- [x] **步骤 1：创建 RoughButton 测试，检查渲染与点击行为**

新建 `frontend/src/components/RoughButton.test.tsx`：

```tsx
// frontend/src/components/RoughButton.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RoughButton from './RoughButton'

describe('RoughButton', () => {
  it('renders children text and handles click', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(<RoughButton onClick={handleClick}>开始观察 →</RoughButton>)

    const button = screen.getByRole('button', { name: '开始观察 →' })
    expect(button).toBeInTheDocument()

    await user.click(button)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

- [x] **步骤 2：运行测试，确认因组件缺失而失败**

```bash
cd frontend
npm run test -- src/components/RoughButton.test.tsx
```

**预期结果：** 测试失败，报错类似 `Cannot find module './RoughButton'`，说明测试已正确捕捉到组件未实现。

### 任务 1.2：实现 RoughButton 组件（GREEN）

- [x] **步骤 3：实现 `RoughButton.tsx`，封装粗风格按钮**

新建 `frontend/src/components/RoughButton.tsx`：

```tsx
// frontend/src/components/RoughButton.tsx
import type { ButtonHTMLAttributes } from 'react'
import styled from 'styled-components'

type RoughButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'teacher' | 'outline' | 'icon'
}

export default function RoughButton({
  variant = 'primary',
  className,
  children,
  ...rest
}: RoughButtonProps) {
  return (
    <Wrapper
      type="button"
      {...rest}
      className={[`rough-button rough-button-${variant}`, className]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </Wrapper>
  )
}

// 只有一个 Wrapper 样式组件，内部通过 className 控制不同变体
const Wrapper = styled.button`
  padding: 12px 32px;
  border: 2px solid #1a1a1a;
  border-radius: 8px;
  font-weight: 700;
  font-size: 16px;
  box-shadow: 4px 4px 0px 0px #1a1a1a;
  cursor: pointer;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;

  &.rough-button-primary {
    background: #2e5cff;
    color: #ffffff;
  }

  &.rough-button-teacher {
    background: #007d5c;
    color: #ffffff;
  }

  &.rough-button-outline {
    background: #ffffff;
    color: #1a1a1a;
  }

  &.rough-button-icon {
    background: transparent;
    color: #1a1c1c;
    padding: 8px;
    border: none;
    box-shadow: none;
    border-radius: 50%;
    font-size: 24px;
  }

  &.rough-button-icon:hover {
    box-shadow: none;
    transform: scale(1.1);
  }

  &.rough-button-icon:active {
    transform: scale(1);
  }

  &:hover {
    box-shadow: 6px 6px 0px 0px #1a1a1a;
    transform: translate(-2px, -2px);
  }

  &:active {
    transform: scale(0.96);
    box-shadow: 2px 2px 0px 0px #1a1a1a;
  }
`
```

- [x] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- src/components/RoughButton.test.tsx
```

**预期结果：** 测试通过，按钮能够渲染并响应点击。

- [x] **步骤 5：（实现时）提交本次改动**

```bash
git add frontend/src/components/RoughButton.tsx frontend/src/components/RoughButton.test.tsx
git commit -m "feat(frontend-landing): 添加全局 RoughButton 粗风格按钮组件"
```

---

## 任务 2：实现 LandingPage 静态布局 + rough-design 视觉（视图在 views）

目标：在不实现真实导航逻辑的前提下，先完成首页的静态布局和 rough-design 视觉效果，严格对齐 demo.html，并使用 `RoughButton` 作为按钮。

**相关文件：**
- 新建：`frontend/src/views/LandingPage.tsx`
- 新建：`frontend/src/views/LandingPage.test.tsx`

### 任务 2.1：为静态渲染编写失败测试（RED）

- [ ] **步骤 1：为 LandingPage 创建基础渲染测试**

新建 `frontend/src/views/LandingPage.test.tsx`，检查首页关键文案是否渲染：

```tsx
// frontend/src/views/LandingPage.test.tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import LandingPage from './LandingPage'

describe('LandingPage', () => {
  it('renders title, subtitle and both mode cards', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    )

    // 主标题 & 副标题
    expect(screen.getByRole('heading', { name: '教学智能体' })).toBeInTheDocument()
    expect(screen.getByText('多Agent教学模拟系统')).toBeInTheDocument()

    // 观察模式卡片（使用 demo.html 原文）
    expect(screen.getByText('观察模式')).toBeInTheDocument()
    expect(
      screen.getByText(
        '进入旁观席位，观察多个AI智能体在模拟课堂中的实时互动、逻辑推演与反馈循环。深入剖析Agent间的协同机制与知识传递路径。',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '开始观察 →' })).toBeInTheDocument()

    // 教师模式卡片（使用 demo.html 原文）
    expect(screen.getByText('教师模式')).toBeInTheDocument()
    expect(
      screen.getByText(
        '扮演引导者角色，直接参与教学模拟。设定教学目标，干预Agent学习进程，并在高保真模拟环境中验证您的教学策略与课程设计。',
      ),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '开始教学 →' })).toBeInTheDocument()

    // 底部技术栈说明
    expect(
      screen.getByText(/技术栈：.*FastAPI.*React.*Qwen.*SQLite/),
    ).toBeInTheDocument()
  })
})
```

- [ ] **步骤 2：运行测试，确认因组件缺失而失败**

```bash
cd frontend
npm run test -- src/views/LandingPage.test.tsx
```

**预期结果：** 测试失败，报错类似 `Cannot find module './LandingPage'`，说明测试已正确捕捉到组件未实现。

### 任务 2.2：实现最小版本的 LandingPage 组件（GREEN）

- [ ] **步骤 3：实现 `LandingPage.tsx` 静态布局 + rough-design 样式（严格对齐 demo.html）**

新建 `frontend/src/views/LandingPage.tsx`。只使用一个 `Wrapper`，内部用 class 嵌套，复用 `RoughButton`，并严格对齐 demo.html 的所有视觉细节：

**关键对齐点（与旧实现的差异）：**
1. 导航栏：实线底边框（非虚线），左侧有 "SimuSketch" 品牌 + 竖线分隔符，右侧使用 Material Icons
2. 卡片边框颜色：观察模式蓝色 `#2e5cff`，教师模式绿色 `#007d5c`（非统一黑色）
3. 教师模式旋转角度：`rotate(1deg)`（非 0.5deg）
4. 卡片描述文案：使用 demo.html 原文（更长更详细）
5. 主标题下方：SVG 波浪线装饰（蓝色）
6. 副标题下方：SVG 虚线装饰（红色）
7. 卡片装饰图标：使用 Material Icons（query_stats、grade、school）
8. Footer：带 skew 的分割线 + 便签风格版本标签（BETA、AI SIMULATION）
9. 背景装饰：固定的 SVG 曲线和圆圈
10. 导航栏右侧：Material Icons（history、settings）+ 头像（而非文字按钮）

```tsx
// frontend/src/views/LandingPage.tsx
import styled from 'styled-components'
import RoughButton from '../components/RoughButton'

export default function LandingPage() {
  return (
    <Wrapper>
      {/* 导航栏 —— 严格对齐 demo.html */}
      <nav className="top-nav">
        <div className="top-nav-left">
          <span className="brand-name">SimuSketch</span>
          <div className="brand-divider" aria-hidden="true" />
          <span className="brand-subtitle">教学智能体</span>
        </div>
        <div className="top-nav-right">
          <button className="nav-icon" aria-label="教学历史" onClick={/* TODO */}>
            <span className="material-symbols-outlined">history</span>
          </button>
          <button className="nav-icon" aria-label="设置">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div className="nav-avatar sketch-shadow">
            {/* TODO: 替换为真实头像 */}
          </div>
        </div>
      </nav>

      {/* 主内容区域 */}
      <main className="main">
        {/* Hero Section —— 带 SVG 装饰 */}
        <header className="hero">
          <h1 className="hero-title">
            教学智能体
            <svg className="hero-underline" viewBox="0 0 100 20" preserveAspectRatio="none" aria-hidden="true">
              <path d="M0 10 Q 25 0, 50 10 T 100 10" fill="transparent" stroke="currentColor" strokeLinecap="round" strokeWidth="4" />
            </svg>
          </h1>
          <p className="hero-subtitle">
            多Agent教学模拟系统
            <svg className="hero-subtitle-line" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true">
              <path d="M0 5 L 100 5" fill="transparent" stroke="currentColor" strokeDasharray="5 5" strokeWidth="2" />
            </svg>
          </p>
        </header>

        {/* 卡片网格 */}
        <section className="mode-grid" aria-label="模式选择">
          {/* 观察模式卡片 */}
          <article className="mode-card observation" aria-label="观察模式">
            <div className="tape tape-left" aria-hidden="true" />
            <div className="card-content">
              <span className="card-icon" aria-hidden="true">👁️</span>
              <h2 className="card-title">观察模式</h2>
              <p className="card-description">
                进入旁观席位，观察多个AI智能体在模拟课堂中的实时互动、逻辑推演与反馈循环。深入剖析Agent间的协同机制与知识传递路径。
              </p>
              <RoughButton variant="primary" className="card-button">
                开始观察 →
              </RoughButton>
            </div>
            <div className="card-decoration card-decoration-observation" aria-hidden="true">
              <span className="material-symbols-outlined">query_stats</span>
            </div>
          </article>

          {/* 教师模式卡片 */}
          <article className="mode-card teacher" aria-label="教师模式">
            <div className="tape tape-right" aria-hidden="true" />
            <div className="star-decoration" aria-hidden="true">
              <span className="material-symbols-outlined star-icon">grade</span>
            </div>
            <div className="card-content">
              <span className="card-icon" aria-hidden="true">👨‍🏫</span>
              <h2 className="card-title">教师模式</h2>
              <p className="card-description">
                扮演引导者角色，直接参与教学模拟。设定教学目标，干预Agent学习进程，并在高保真模拟环境中验证您的教学策略与课程设计。
              </p>
              <RoughButton variant="teacher" className="card-button">
                开始教学 →
              </RoughButton>
            </div>
            <div className="card-decoration card-decoration-teacher" aria-hidden="true">
              <span className="material-symbols-outlined">school</span>
            </div>
          </article>
        </section>
      </main>

      {/* 背景装饰 SVG */}
      <div className="bg-decoration bg-decoration-left" aria-hidden="true">
        <svg height="200" viewBox="0 0 100 100" width="200">
          <path d="M10,50 Q30,10 50,50 T90,50" fill="none" stroke="#2E5CFF" strokeDasharray="4 2" strokeWidth="2" />
        </svg>
      </div>
      <div className="bg-decoration bg-decoration-right" aria-hidden="true">
        <svg height="200" viewBox="0 0 100 100" width="200">
          <circle cx="50" cy="50" fill="none" r="40" stroke="#E63946" strokeDasharray="8 4" strokeWidth="2" />
        </svg>
      </div>

      {/* Footer —— 严格对齐 demo.html */}
      <footer className="footer">
        <div className="footer-divider" aria-hidden="true">
          <div className="footer-divider-skew" />
        </div>
        <p className="footer-text">
          技术栈：<span className="footer-highlight">FastAPI</span> + <span className="footer-highlight">React</span> + <span className="footer-highlight">Qwen</span> + <span className="footer-highlight">SQLite</span>
        </p>
        <div className="footer-tags">
          <div className="footer-tag footer-tag-beta sketch-shadow">BETA v0.8.2</div>
          <div className="footer-tag footer-tag-ai sketch-shadow">AI SIMULATION</div>
        </div>
      </footer>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100vh;
  width: 100%;
  background: #f9f9f9;
  color: #1a1c1c;
  color-scheme: light;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: 'Be Vietnam Pro', system-ui, -apple-system, BlinkMacSystemFont,
    sans-serif;

  /* ===== 导航栏 ===== */
  .top-nav {
    position: sticky;
    top: 0;
    z-index: 50;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: #fafafa;
    border-bottom: 2px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
  }

  .top-nav-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .brand-name {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-weight: 900;
    font-size: 24px;
    text-decoration: underline wavy #2e5cff;
    text-underline-offset: 4px;
  }

  .brand-divider {
    width: 2px;
    height: 24px;
    background: #1a1a1a;
    transform: rotate(12deg);
  }

  .brand-subtitle {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-weight: 700;
    font-size: 18px;
    letter-spacing: -0.5px;
  }

  .top-nav-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .nav-icon {
    background: transparent;
    border: none;
    cursor: pointer;
    color: #1a1c1c;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    transition: transform 0.2s ease;

    &:hover {
      transform: scale(1.1);
    }
  }

  .nav-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid #1a1a1a;
    overflow: hidden;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    background: #e2e2e2;
  }

  .sketch-shadow {
    box-shadow: 4px 4px 0px 0px #1a1a1a;
  }

  /* ===== 主内容区 ===== */
  .main {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
    padding: 64px 24px;
    min-height: calc(100vh - 80px);
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* ===== Hero Section ===== */
  .hero {
    text-align: center;
    margin-bottom: 80px;
  }

  .hero-title {
    position: relative;
    display: inline-block;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 48px;
    font-weight: 900;
    margin-bottom: 16px;
    color: #1a1c1c;
  }

  .hero-underline {
    position: absolute;
    bottom: -8px;
    left: 0;
    width: 100%;
    height: 16px;
    color: #2e5cff;
  }

  .hero-subtitle {
    position: relative;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    color: #525252;
    margin-top: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .hero-subtitle-line {
    width: 192px;
    height: 8px;
    color: #b7102a;
    margin-top: 8px;
  }

  /* ===== 卡片网格 ===== */
  .mode-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 48px;
    width: 100%;
    max-width: 1024px;

    @media (min-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  /* ===== 卡片通用 ===== */
  .mode-card {
    position: relative;
    border: 3px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 40px;
    transition: all 0.3s ease;

    &:hover {
      box-shadow: 8px 8px 0px 0px #1a1a1a;
      transform: translate(-4px, -4px);
    }
  }

  .mode-card.observation {
    background: #e3f2fd;
    border-color: #2e5cff;
    transform: rotate(-0.5deg);

    &:hover {
      transform: translate(-4px, -4px) rotate(-0.5deg);
    }
  }

  .mode-card.teacher {
    background: #e8f5e9;
    border-color: #007d5c;
    transform: rotate(1deg);

    &:hover {
      transform: translate(-4px, -4px) rotate(1deg);
    }
  }

  /* ===== 胶带 ===== */
  .tape {
    position: absolute;
    top: -16px;
    width: 64px;
    height: 32px;
    background: rgba(227, 242, 253, 0.6);
    backdrop-filter: blur(1px);
    border-left: 1px solid rgba(200, 200, 200, 0.3);
    border-right: 1px solid rgba(200, 200, 200, 0.3);
  }

  .tape-left {
    left: -8px;
    transform: rotate(-15deg);
  }

  .tape-right {
    right: -8px;
    transform: rotate(15deg);
  }

  /* ===== 卡片内容 ===== */
  .card-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .card-icon {
    font-size: 48px;
    display: block;
    margin-bottom: 16px;
  }

  .card-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 32px;
    font-weight: 900;
    color: #171717;
    margin-bottom: 16px;
  }

  .card-description {
    font-size: 18px;
    color: #404040;
    line-height: 1.625;
    margin-bottom: 32px;
  }

  .card-button {
    align-self: flex-start;
  }

  /* ===== 卡片装饰 ===== */
  .card-decoration {
    position: absolute;
    bottom: 16px;
    right: 16px;
    opacity: 0.1;
    pointer-events: none;
    transition: opacity 0.2s ease;

    .material-symbols-outlined {
      font-size: 60px;
    }
  }

  .mode-card:hover .card-decoration {
    opacity: 0.2;
  }

  .star-decoration {
    position: absolute;
    top: 16px;
    right: 16px;
    transform: rotate(12deg);

    .star-icon {
      font-size: 30px;
      color: #27e0a9;
      font-variation-settings: 'FILL' 1;
    }
  }

  /* ===== 背景装饰 ===== */
  .bg-decoration {
    position: fixed;
    opacity: 0.2;
    pointer-events: none;
    z-index: -10;
  }

  .bg-decoration-left {
    top: 25%;
    left: -48px;
  }

  .bg-decoration-right {
    bottom: 25%;
    right: -48px;
  }

  /* ===== Footer ===== */
  .footer {
    width: 100%;
    padding: 48px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
  }

  .footer-divider {
    width: 100%;
    max-width: 896px;
    height: 2px;
    background: #d4d4d4;
    position: relative;
    overflow: hidden;
  }

  .footer-divider-skew {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #d4d4d4;
    transform: scaleY(0.5) skewX(12deg);
  }

  .footer-text {
    font-size: 14px;
    font-weight: 500;
    color: #747688;
    letter-spacing: 0.5px;
  }

  .footer-highlight {
    color: #171717;
    font-weight: 700;
  }

  .footer-tags {
    display: flex;
    gap: 16px;
  }

  .footer-tag {
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #1a1a1a;
  }

  .footer-tag-beta {
    background: #fce4ec;
    transform: rotate(2deg);
  }

  .footer-tag-ai {
    background: #fff9c4;
    transform: rotate(-1deg);
  }

  /* ===== 响应式 ===== */
  @media (max-width: 768px) {
    .main {
      padding: 32px 16px;
      min-height: auto;
    }

    .hero {
      margin-bottom: 40px;
    }

    .hero-title {
      font-size: 36px;
    }

    .hero-subtitle {
      font-size: 20px;
    }

    .mode-grid {
      gap: 32px;
    }

    .mode-card {
      padding: 24px;
    }

    .brand-name {
      font-size: 20px;
    }
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- src/views/LandingPage.test.tsx src/components/RoughButton.test.tsx
```

**预期结果：** 测试全部通过，说明首页静态布局和文案已正确渲染，按钮组件可用。

- [ ] **步骤 5：（实现时）提交本次改动**

```bash
git add frontend/src/views/LandingPage.tsx frontend/src/views/LandingPage.test.tsx
git commit -m "feat(frontend-landing): 实现 rough 风格首页静态布局（严格对齐 demo.html）"
```

---

## 任务 3：让 App.tsx 使用 React Router 渲染 LandingPage

目标：移除现有计数器 demo，使 `App` 成为路由容器，通过 `react-router-dom` 在 `/` 路由渲染真正的模式选择首页。

**相关文件：**
- 修改：`frontend/src/App.tsx`
- 修改：`frontend/src/main.tsx`
- 新增测试：`frontend/src/App.test.tsx`

### 任务 3.1：为 App 渲染首页编写失败测试（RED）

- [x] **步骤 1：创建 App 测试，断言在 `/` 路由下出现首页内容**

新建 `frontend/src/App.test.tsx`：

```tsx
// frontend/src/App.test.tsx
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders landing page title and modes on root route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: '教学智能体' })).toBeInTheDocument()
    expect(screen.getByText('多Agent教学模拟系统')).toBeInTheDocument()
    expect(screen.getByText('观察模式')).toBeInTheDocument()
    expect(screen.getByText('教师模式')).toBeInTheDocument()
  })
})
```

- [x] **步骤 2：运行 App 测试，确认当前实现失败**

```bash
cd frontend
npm run test -- src/App.test.tsx
```

### 任务 3.2：修改 main.tsx 与 App.tsx 使用 BrowserRouter + Routes（GREEN）

- [x] **步骤 3：修改 `main.tsx`，在入口包裹 `BrowserRouter`**

更新 `frontend/src/main.tsx`：

```tsx
// frontend/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

- [x] **步骤 4：修改 `App.tsx`，作为路由容器渲染 LandingPage**

更新 `frontend/src/App.tsx`：

```tsx
// frontend/src/App.tsx
import styled from 'styled-components'
import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'

export default function App() {
  return (
    <Wrapper>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* 预留后续页面路由占位 */}
      </Routes>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100vh;
  background: #f9f9f9;
  color-scheme: light;
`
```

- [x] **步骤 5：运行 App + LandingPage 测试，确认通过**

```bash
cd frontend
npm run test -- src/App.test.tsx src/views/LandingPage.test.tsx src/components/RoughButton.test.tsx
```

- [x] **步骤 6：（实现时）提交改动**

```bash
git add frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/main.tsx
git commit -m "feat(frontend-landing): 引入 react-router 并在 / 渲染首页"
```

---

## 任务 4：为模式按钮添加 useNavigate 跳转逻辑

目标：点击「开始观察 →」跳转到 `/observation/config`，点击「开始教学 →」跳转到 `/teacher/config`，使用 `react-router-dom` 提供的 `useNavigate`。

**相关文件：**
- 修改：`frontend/src/views/LandingPage.tsx`
- 修改：`frontend/src/views/LandingPage.test.tsx`

### 任务 4.1：为按钮点击行为编写失败测试（RED）

- [x] **步骤 1：在测试中检查按钮点击时调用正确路径**

```tsx
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

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

it('navigates to observation config when clicking 开始观察', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter><LandingPage /></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: '开始观察 →' }))
  expect(mockNavigate).toHaveBeenCalledWith('/observation/config')
})

it('navigates to teacher config when clicking 开始教学', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter><LandingPage /></MemoryRouter>)
  await user.click(screen.getByRole('button', { name: '开始教学 →' }))
  expect(mockNavigate).toHaveBeenCalledWith('/teacher/config')
})
```

### 任务 4.2：在 LandingPage 中实现按钮点击跳转逻辑（GREEN）

- [x] **步骤 3：在 LandingPage 中引入 `useNavigate` 并绑定按钮**

```tsx
import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const navigate = useNavigate()

  const handleGoObservation = () => navigate('/observation/config')
  const handleGoTeacher = () => navigate('/teacher/config')
  // ...
}
```

---

## 任务 5：实现导航栏按钮行为

目标：为导航栏 history 图标添加 `useNavigate` 行为（跳转 `/history`），settings 图标暂不绑定（后续计划），GitHub 通过 `window.open` 打开（demo.html 中无 GitHub 按钮，但保留需求）。

**相关文件：**
- 修改：`frontend/src/views/LandingPage.tsx`
- 修改：`frontend/src/views/LandingPage.test.tsx`

### 任务 5.1：为导航栏按钮编写失败测试（RED）

- [x] **步骤 1：在测试中检查导航栏 history 图标行为**

```tsx
it('navigates to history page when clicking history icon', async () => {
  const user = userEvent.setup()
  render(<MemoryRouter><LandingPage /></MemoryRouter>)
  await user.click(screen.getByLabelText('教学历史'))
  expect(mockNavigate).toHaveBeenCalledWith('/history')
})
```

### 任务 5.2：实现导航栏按钮逻辑（GREEN）

- [x] **步骤 3：绑定 onClick**

```tsx
<button className="nav-icon" aria-label="教学历史" onClick={() => navigate('/history')}>
  <span className="material-symbols-outlined">history</span>
</button>
```

---

## 任务 6：rough-design 视觉一致性检查与小测试

目标：确保最终视觉效果与 `demo.html` 一致。

**相关文件：**
- 可能修改：`frontend/src/views/LandingPage.tsx`
- 可选测试增强：`frontend/src/views/LandingPage.test.tsx`

### 任务 6.1：增加结构元素测试

- [ ] **步骤 1：检查关键 rough 元素是否存在**

```tsx
it('uses rough design elements like tape, decorations, and footer tags', () => {
  render(<MemoryRouter><LandingPage /></MemoryRouter>)

  expect(document.querySelectorAll('.tape').length).toBeGreaterThanOrEqual(1)
  expect(document.querySelectorAll('.card-decoration').length).toBeGreaterThanOrEqual(1)
  expect(document.querySelectorAll('.footer-tag').length).toBeGreaterThanOrEqual(1)
  expect(document.querySelector('.brand-name')?.textContent).toBe('SimuSketch')
  expect(document.querySelector('.bg-decoration-left')).toBeInTheDocument()
})
```

### 任务 6.2：手动视觉检查，与 demo.html 对照（REFACTOR）

- [ ] **步骤 3：启动 dev server，浏览器中与 demo.html 并排对比**

```bash
cd frontend
npm run dev
```

对照清单（与 demo.html 逐项对比）：

- [ ] 导航栏：实线底边框（非虚线），`SimuSketch` wavy underline + 竖线 + `教学智能体`
- [ ] 导航栏右侧：Material Icons history/settings + 圆形头像
- [ ] 主标题下方：蓝色 SVG 波浪线装饰
- [ ] 副标题下方：红色 SVG 虚线装饰
- [ ] 观察模式卡片：蓝色边框 `#2e5cff`（非黑色），`rotate(-0.5deg)`
- [ ] 教师模式卡片：绿色边框 `#007d5c`（非黑色），`rotate(1deg)`（非 0.5deg）
- [ ] 教师模式右上角：绿色 grade 星星装饰（filled, rotate 12deg）
- [ ] 卡片右下角：Material Icons 装饰（query_stats / school）
- [ ] 卡片描述文案：使用 demo.html 原文
- [ ] Footer：带 skew 分割线 + 技术栈关键词加粗 + BETA/AI SIMULATION 便签标签
- [ ] 背景装饰：左侧蓝色曲线 + 右侧红色圆圈（fixed 定位）
- [ ] 响应式：768px 以下卡片变单列

---

## 功能完成前的最终检查清单

在宣告「前端首页（Landing Page）开发完成」之前，请确保：

- [ ] `npm run test -- src/components/RoughButton.test.tsx src/views/LandingPage.test.tsx src/App.test.tsx` 全部通过
- [ ] 在 `frontend/` 中运行 `npm run lint` 无错误
- [ ] 实际页面布局与 `docs/frontend-design-prompts/demo.html` 视觉一致
- [ ] 页面明显呈现 rough-design 风格：粗边框（彩色）、硬阴影、胶带、便签色、轻微旋转、Material Icons 装饰、SVG 波浪线、背景装饰、便签标签等
- [ ] 导航栏品牌名 "SimuSketch" 带 wavy underline，右侧使用 Material Icons
- [ ] 卡片边框颜色区分：观察模式蓝色、教师模式绿色（非统一黑色）
- [ ] 卡片描述使用 demo.html 原文（更长更详细）
- [ ] Footer 包含 BETA 版本标签和 AI SIMULATION 便签标签
- [ ] 背景有固定的 SVG 装饰元素
- [ ] 「开始观察 →」「开始教学 →」按钮通过 `useNavigate` 跳转至预期 URL
- [ ] 导航栏 history 图标通过 `useNavigate` 跳转 `/history`
- [ ] `App.tsx` 使用 `Routes` / `Route` 渲染 `/` 路由，`main.tsx` 在入口使用 `BrowserRouter` 包裹

当以上检查全部通过，并使用约定格式的中文 commit message 提交后，即可认为 **基于 react-router 的 rough-design 风格前端首页（严格对齐 demo.html）** 已按 TDD 流程实现完成。
