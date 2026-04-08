# 白板草图风格指南

## 整体视觉风格定义

### 核心理念
采用白板草图风格（Whiteboard Sketch Style），营造教学研讨的轻松氛围。所有页面呈现为在白色/浅灰色背景上用马克笔手绘的设计稿，辅以彩色便签和箭头标注。

### 视觉特征
- **背景色**：纯白色 `#FFFFFF` 或极浅灰色 `#FAFAFA`
- **线条风格**：马克笔粗线条（2-3px），手绘不规则边缘
- **阴影**：硬阴影，向右下偏移 4px，模糊度 0px
- **边框**：不规则手绘边框，略带抖动感

## 色彩系统

### 白板底色
```css
--bg-primary: #FFFFFF
--bg-secondary: #FAFAFA
--bg-tertiary: #F0F0F0
```

### 马克笔色系（用于线条、文字、图标）
```css
--marker-black: #1A1A1A    /* 主要文字、边框 */
--marker-blue: #2E5CFF     /* 蓝色强调、链接 */
--marker-red: #E63946      /* 红色警告、错误 */
--marker-green: #06D6A0    /* 绿色成功、完成 */
--marker-orange: #FB8500   /* 橙色警告、待办 */
--marker-purple: #9D4EDD   /* 紫色特殊标注 */
--marker-gray: #6C757D     /* 次要文字、占位符 */
```

### 便签色系（用于卡片、标签、背景块）
```css
--sticky-yellow: #FFF9C4   /* 黄色便签 - 默认卡片 */
--sticky-blue: #E3F2FD     /* 蓝色便签 - 信息提示 */
--sticky-green: #E8F5E9    /* 绿色便签 - 成功状态 */
--sticky-orange: #FFF3E0   /* 橙色便签 - 警告提示 */
--sticky-pink: #FCE4EC     /* 粉色便签 - 特殊标注 */
--sticky-purple: #F3E5F5   /* 紫色便签 - 高级功能 */
```

### 状态色
```css
--state-pending: #FFE0B2   /* 待处理 - 浅橙 */
--state-teaching: #BBDEFB  /* 进行中 - 浅蓝 */
--state-questions: #E1BEE7 /* 提问中 - 浅紫 */
--state-complete: #C8E6C9  /* 已完成 - 浅绿 */
--state-error: #FFCDD2     /* 错误 - 浅红 */
```

## 字体系统

### 字体族
```css
--font-family: 'Comic Sans MS', 'YouYuan', '幼圆', 'STKaiti', '华文楷体', sans-serif
--font-family-title: 'YouYuan', '幼圆', 'STKaiti', '华文楷体', sans-serif
--font-family-mono: 'Courier New', monospace
```

### 字号规范
```css
--font-size-title: 48px         /* 主标题 */
--font-size-subtitle: 32px      /* 副标题 */
--font-size-heading: 24px       /* 区域标题 */
--font-size-body: 16px          /* 正文 */
--font-size-caption: 14px       /* 辅助文字 */
--font-size-small: 12px         /* 小字说明 */
```

### 字重
```css
--font-weight-bold: 700         /* 粗体标题 */
--font-weight-medium: 500       /* 中等强调 */
--font-weight-regular: 400      /* 常规正文 */
--font-weight-light: 300        /* 轻量说明 */
```

## 组件规范

### 按钮（手绘风格）

**主按钮（Primary Button）**
```css
/* 样式 */
background: var(--sticky-blue)
border: 3px solid var(--marker-blue)
border-radius: 8px /* 不规则圆角 */
box-shadow: 4px 4px 0px var(--marker-blue)
color: var(--marker-black)
font-weight: var(--font-weight-bold)
padding: 12px 32px

/* 悬停状态 */
transform: translate(-2px, -2px)
box-shadow: 6px 6px 0px var(--marker-blue)

/* 点击状态 */
transform: translate(0, 0)
box-shadow: 2px 2px 0px var(--marker-blue)
```

**次要按钮（Secondary Button）**
```css
background: var(--sticky-yellow)
border: 3px solid var(--marker-black)
border-radius: 8px
box-shadow: 4px 4px 0px var(--marker-black)
color: var(--marker-black)
```

**危险按钮（Danger Button）**
```css
background: var(--sticky-pink)
border: 3px solid var(--marker-red)
box-shadow: 4px 4px 0px var(--marker-red)
color: var(--marker-red)
```

### 卡片（便签风格）

**基础卡片**
```css
background: var(--sticky-yellow)
border: 2px solid var(--marker-black)
border-radius: 4px /* 略微不规则 */
box-shadow: 3px 3px 0px rgba(0, 0, 0, 0.2)
padding: 20px

/* 卡片标题 */
.card-title {
  font-size: var(--font-size-heading)
  font-weight: var(--font-weight-bold)
  margin-bottom: 12px
  border-bottom: 2px dashed var(--marker-gray)
  padding-bottom: 8px
}
```

**状态卡片**
- PENDING: 橙色背景 `var(--sticky-orange)`
- TEACHING: 蓝色背景 `var(--sticky-blue)`
- QUESTIONS: 紫色背景 `var(--sticky-purple)`
- COMPLETE: 绿色背景 `var(--sticky-green)`

### 输入框（手绘风格）

```css
background: white
border: 2px solid var(--marker-gray)
border-radius: 4px
padding: 10px 14px
font-size: var(--font-size-body)
transition: all 0.2s

/* 聚焦状态 */
&:focus {
  border-color: var(--marker-blue)
  border-width: 3px
  outline: none
  box-shadow: 3px 3px 0px var(--marker-blue)
}

/* 占位符 */
&::placeholder {
  color: var(--marker-gray)
  font-style: italic
}
```

### 标签（Tags）

**基础标签**
```css
display: inline-block
padding: 4px 12px
border-radius: 12px
font-size: var(--font-size-small)
font-weight: var(--font-weight-medium)
background: var(--bg-tertiary)
border: 2px solid var(--marker-gray)
```

**彩色标签**
- **观察模式**：蓝色标签 `background: var(--sticky-blue); border-color: var(--marker-blue)`
- **教师模式**：绿色标签 `background: var(--sticky-green); border-color: var(--marker-green)`
- **灌输式**：黄色标签 `background: var(--sticky-yellow); border-color: var(--marker-orange)`
- **启发式**：紫色标签 `background: var(--sticky-purple); border-color: var(--marker-purple)`
- **讨论式**：粉色标签 `background: var(--sticky-pink); border-color: var(--marker-red)`

### 徽章（Badges）

```css
/* 数字徽章 */
display: inline-flex
align-items: center
justify-content: center
min-width: 24px
height: 24px
padding: 0 6px
border-radius: 12px
background: var(--marker-red)
color: white
font-size: var(--font-size-small)
font-weight: var(--font-weight-bold)
border: 2px solid var(--marker-black)
```

### 进度条（手绘风格）

```css
/* 容器 */
background: var(--bg-tertiary)
border: 2px solid var(--marker-gray)
border-radius: 12px
height: 24px
overflow: hidden
position: relative

/* 进度填充 */
.progress-fill {
  background: linear-gradient(90deg, var(--marker-green), #4ADE80)
  border-right: 2px solid var(--marker-black)
  height: 100%
  transition: width 0.3s ease
}

/* 进度文字 */
.progress-text {
  position: absolute
  top: 50%
  left: 50%
  transform: translate(-50%, -50%)
  font-weight: var(--font-weight-bold)
  font-size: var(--font-size-caption)
  text-shadow: 1px 1px 0px white
}
```

## 布局网格

### 容器规范
```css
/* 主容器 */
.container {
  max-width: 1280px
  margin: 0 auto
  padding: 0 24px
}

/* 内边距 */
--spacing-xs: 4px
--spacing-sm: 8px
--spacing-md: 16px
--spacing-lg: 24px
--spacing-xl: 32px
--spacing-2xl: 48px
--spacing-3xl: 64px
```

### 网格间距
```css
/* 卡片网格 */
.grid {
  display: grid
  gap: var(--spacing-lg)
}

/* 两列布局 */
.grid-2 {
  grid-template-columns: repeat(2, 1fr)
}

/* 三列布局 */
.grid-3 {
  grid-template-columns: repeat(3, 1fr)
}

/* 四列布局 */
.grid-4 {
  grid-template-columns: repeat(4, 1fr)
}
```

## 图标风格

### 图标规范
- 使用手绘线条风格图标
- 线条粗细：2px
- 颜色：主要使用 `var(--marker-black)`
- 特殊状态使用对应颜色（成功用绿色，错误用红色）

### 推荐图标集
- 手绘风格：Hand Drawn Icons
- 备选：Noto Color Emoji, Emoji One

### 常用图标
- 🏠 首页
- 👁️ 观察
- 👨‍🏫 教师
- ⚙️ 设置
- 📊 统计
- ✅ 完成
- ⏳ 待处理
- ❌ 错误
- ➕ 添加
- ✏️ 编辑
- 🗑️ 删除
- 🔙 返回
- ▶️ 播放
- ⏸️ 暂停
- 📤 发送

## 特殊元素

### 箭头标注
```css
/* 指向性箭头 */
.arrow-pointer {
  position: relative
  &::after {
    content: '→'
    position: absolute
    right: -20px
    font-size: 24px
    color: var(--marker-red)
  }
}

/* 手绘箭头 SVG */
.arrow-sketch {
  stroke: var(--marker-black)
  stroke-width: 3
  fill: none
  filter: drop-shadow(2px 2px 0px rgba(0, 0, 0, 0.1))
}
```

### 胶带效果（用于粘贴便签）
```css
.tape {
  position: absolute
  top: -12px
  left: 50%
  transform: translateX(-50%) rotate(-2deg)
  width: 80px
  height: 24px
  background: rgba(255, 255, 255, 0.4)
  border-left: 1px dashed rgba(0, 0, 0, 0.1)
  border-right: 1px dashed rgba(0, 0, 0, 0.1)
}
```

### 涂改痕迹
```css
.scribble {
  position: relative
  &::before {
    content: ''
    position: absolute
    top: -5px
    left: -5px
    right: -5px
    bottom: -5px
    border: 2px solid var(--marker-red)
    border-radius: 50% 40% 60% 30% / 40% 50% 60% 50%
    transform: rotate(-3deg)
  }
}
```

## 页面模板引用

所有页面设计提示词应引用本风格指南：

```markdown
---
视觉风格：遵循 style-guide.md 定义的**白板草图风格**
---

## 页面描述
[页面具体描述...]

## 布局结构
[布局说明...]

## 组件列表
- 使用基础卡片（引用 style-guide.md 卡片规范）
- 使用主按钮（引用 style-guide.md 按钮规范）
[...]

## 交互说明
[交互描述...]

## 示例数据
[示例数据...]
```

## 设计原则

1. **一致性优先**：所有页面保持统一的手绘风格和色彩系统
2. **功能优先**：装饰元素不干扰内容阅读和操作
3. **视觉层次**：通过颜色、大小、阴影建立清晰的视觉层级
4. **可访问性**：保持足够的对比度，确保文字可读性
5. **友好氛围**：营造轻松、亲切的教学研讨氛围
