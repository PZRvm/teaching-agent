# 教学智能体 (Teaching AI Agent)

基于 AI 的教学模拟系统，支持观察模式和教师模式两种应用场景。

## 项目概述

- **观察模式**: 用户观察 AI 教师和 AI 学生自动教学过程，用于教育研究
- **教师模式**: 用户扮演教师，控制 AI 学生进行教学

## 技术栈

### 后端
- Python 3.12+
- FastAPI - Web 框架
- SQLAlchemy - ORM
- Alembic - 数据库迁移
- SQLite - 数据库
- Pydantic - 数据验证

### 前端
- React 18
- TypeScript
- Vite
- Styled-components

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 20+
- SQLite 3

### 后端设置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 启动开发服务器
python main.py
```

后端运行在 `http://0.0.0.0:8000`

### 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 `http://localhost:5173`

## 数据库迁移 (Alembic)

### 初始化迁移

首次设置项目时，运行以下命令创建数据库表：

```bash
cd backend
alembic upgrade head
```

### 创建新迁移

当修改 ORM 模型后，生成新的迁移脚本：

```bash
alembic revision --autogenerate -m "描述变更内容"
```

### 应用迁移

将待执行的迁移应用到数据库：

```bash
alembic upgrade head
```

### 回滚迁移

回滚到上一个迁移版本：

```bash
alembic downgrade -1
```

### 查看迁移状态

查看已应用的迁移版本：

```bash
alembic current
```

查看迁移历史：

```bash
alembic history
```

### 数据库位置

SQLite 数据库文件位于：`backend/datas/database.db`

### 外键约束说明

SQLite 默认不强制执行外键约束。项目在 Alembic 环境配置中已启用外键约束检查，但在使用其他 SQLite 客户端时，需要手动执行：

```sql
PRAGMA foreign_keys = ON;
```

## 开发

### 代码规范

- 后端：使用 `ruff` 进行代码检查和格式化
  ```bash
  ruff check .          # 检查
  ruff check . --fix    # 自动修复
  ruff format .         # 格式化
  ```

- 前端：使用 ESLint 进行代码检查
  ```bash
  npm run lint
  ```

### 测试

- 后端测试（pytest）：
  ```bash
  cd backend
  pytest tests/ -v
  ```

- 前端测试（vitest）：
  ```bash
  cd frontend
  npm run test
  ```

## 项目结构

```
.
├── backend/                 # 后端代码
│   ├── agents/             # AI Agent 实现
│   ├── alembic/            # 数据库迁移脚本
│   │   └── versions/       # 迁移版本文件
│   ├── core/               # 核心业务逻辑
│   ├── datas/              # 数据文件
│   │   └── database.db     # SQLite 数据库
│   ├── models/             # API 路由和服务
│   ├── orm/                # ORM 模型
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # 业务服务
│   └── tests/              # 后端测试
│       ├── conftest.py     # pytest fixtures
│       ├── test_database.py
│       ├── test_schemas.py
│       └── test_alembic_migration.py
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── apis/          # API 客户端
│   │   ├── components/    # React 组件
│   │   └── hooks/         # 自定义 hooks
│   └── tests/             # 前端测试
├── docs/                   # 项目文档
│   └── tests/             # 测试文档
└── README.md
```

## 开发路线图

详见 [docs/development-roadmap.md](docs/development-roadmap.md)

## 许可证

MIT License
