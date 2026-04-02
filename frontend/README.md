# 教学智能体 - 前端

基于 React 19 + TypeScript + Vite 构建的教学智能体系统前端。

## 技术栈

- **React 19** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Styled Components** - CSS-in-JS 样式方案
- **React Compiler** - 自动优化（通过 Babel 插件）

## 目录结构

```
frontend/
├── src/
│   ├── apis/          # API 接口封装
│   ├── components/    # React 组件
│   ├── assets/        # 静态资源
│   ├── App.tsx        # 根组件
│   ├── main.tsx       # 入口文件
│   └── ...            # 其他文件
├── public/            # 公共静态资源
├── index.html         # HTML 模板
├── vite.config.ts     # Vite 配置
├── tsconfig.json      # TypeScript 配置
└── package.json       # 依赖管理
```

## 开发命令

```bash
# 安装依赖
npm install

# 启动开发服务器 (http://localhost:5173)
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

## 代码规范

### 组件编写规范

所有组件统一使用以下格式（只使用一个 Wrapper 样式组件）：

```tsx
// 组件文件示例
import styled from 'styled-components'

export default function MyComponent() {
  // 组件逻辑...

  return (
    <Wrapper>
      <div className="header">标题</div>
      <div className="content">
        <p className="text">内容</p>
      </div>
    </Wrapper>
  )
}

// 只有一个 Wrapper 样式组件
// 内部使用 class 选择器，支持多层嵌套
const Wrapper = styled.div`
  padding: 20px;

  .header {
    font-size: 24px;
    color: #333;
  }

  .content {
    padding: 10px;

    .text {
      font-size: 16px;
      color: #666;
    }
  }
`
```

### 命名规范

- 组件文件：PascalCase（如 `UserProfile.tsx`）
- Wrapper 样式组件：统一命名为 `Wrapper`
- 内部 class：kebab-case（如 `header`、`content`、`user-name`）
- 工具函数：camelCase（如 `fetchUserData`）

