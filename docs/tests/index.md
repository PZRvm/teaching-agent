# 自动化测试文档

本文档描述了项目的自动化测试体系，包括后端测试、前端测试和 E2E 测试。

## 测试概述

| 测试类型 | 框架 | 覆盖率目标 | 状态 |
|---------|------|------------|------|
| 后端单元测试 | pytest + pytest-asyncio | >60% | ✅ 已实现 |
| 前端单元测试 | vitest + @testing-library/react | >60% | 🚧 待实现 |
| E2E 测试 | Playwright (可选) | 核心流程 | ❌ 未实现 |

## 测试文档导航

- **[后端测试详细文档](./backend/index.md)** - pytest 测试框架、fixtures、测试用例说明
- **[前端测试详细文档](./frontend/index.md)** - vitest 测试框架、组件测试说明
- **[E2E 测试文档](./e2e/index.md)** - 端到端测试指南

---

## 快速开始

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_database.py

# 生成覆盖率报告
pytest --cov=backend --cov-report=term-missing
```

详细说明见 [后端测试文档](./backend/index.md)

### 前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行测试并监听变化
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

详细说明见 [前端测试文档](./frontend/index.md)

### E2E 测试

```bash
# 使用 Playwright（如果已安装）
npx playwright test

# 查看测试报告
npx playwright show-report
```

详细说明见 [E2E 测试文档](./e2e/index.md)

---

## 测试覆盖率总览

### 后端测试

| 模块 | 测试文件 | 测试数量 | 覆盖率 |
|------|---------|---------|--------|
| ORM 模型 | `test_database.py` | 6 | >80% ✅ |
| Schema 验证 | `test_schemas.py` | 18 | >90% ✅ |
| Memory 系统 | 待添加 | - | - |
| StudentFactory | 待添加 | - | - |
| Agent 系统 | 待添加 | - | - |
| API 端点 | 待添加 | - | - |

**当前后端测试总数**: 24 个

### 前端测试

| 类型 | 测试文件 | 测试数量 | 状态 |
|------|---------|---------|------|
| 组件测试 | 待添加 | - | 🚧 |
| Hooks 测试 | 待添加 | - | 🚧 |
| 工具函数 | 待添加 | - | 🚧 |

---

## 持续集成 (CI)

### GitHub Actions 配置示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      - name: Run tests
        run: |
          cd frontend
          npm run test:coverage
```

---

## 测试最佳实践

### 1. TDD (测试驱动开发)

遵循 Red-Green-Refactor 循环：
1. **Red** - 先写失败的测试
2. **Green** - 写最少的代码让测试通过
3. **Refactor** - 重构改进代码

### 2. 测试命名规范

```python
# ✅ 好的测试名称
def test_create_teaching_session_with_valid_data():
    """测试：使用有效数据创建教学会话"""
    pass

# ❌ 避免的测试名称
def test1():
    pass
```

### 3. AAA 模式

- **Arrange** - 准备测试数据
- **Act** - 执行被测试的操作
- **Assert** - 验证结果

### 4. 测试隔离

- 每个测试应该独立运行
- 不依赖测试执行顺序
- 使用 fixture 设置独立的测试环境

### 5. Mock 使用原则

- 优先测试真实行为
- 只 mock 外部依赖（API 调用）
- 测试内部逻辑时使用真实实现

---

## 常见问题

### Q: 如何调试失败的测试？

```bash
# 后端测试 - 详细输出
pytest tests/test_database.py::test_name -vv

# 后端测试 - 使用 pdb 调试器
pytest tests/test_database.py::test_name --pdb

# 前端测试 - 使用 UI 模式
npm run test:ui
```

### Q: 数据库测试太慢？

- 使用内存数据库（已配置）
- 并行运行：`pytest -n auto`
- 跳过慢速测试：`pytest -m "not slow"`

### Q: 前端测试环境变量未定义？

在 `vitest.config.ts` 中设置：
```typescript
export default defineConfig({
  env: {
    VITE_API_URL: 'http://localhost:8000',
  },
})
```

更多问题和解决方案，请查看各测试类型的详细文档：
- [后端测试常见问题](./backend/index.md#常见问题)
- [前端测试常见问题](./frontend/index.md#常见问题)
- [E2E 测试常见问题](./e2e/index.md#常见问题)
