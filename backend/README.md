# 教学智能体 - 后端

基于 FastAPI + LangChain 构建的教学智能体系统后端。

## 技术栈

- **FastAPI** - 高性能 Web 框架
- **LangChain** - AI/LLM 应用开发框架
- **硅基流动 / OpenAI SDK** - 大语言模型接口（兼容 OpenAI 格式）
- **PostgreSQL** - 关系型数据库（通过 asyncpg 异步驱动）
- **SQLAlchemy** - ORM 数据库操作
- **Alembic** - 数据库迁移工具
- **Uvicorn** - ASGI 服务器

## 目录结构

```
backend/
├── models/              # 功能模块（路由 + 业务逻辑）
│   ├── user/           # 用户模块
│   │   ├── router.py
│   │   └── service.py
│   ├── session/        # 教学会话模块
│   │   ├── router.py
│   │   └── service.py
│   └── observation/    # 观察模式模块
│       ├── router.py
│       └── service.py
├── orm/                # 数据库ORM模型
│   ├── __init__.py
│   ├── teaching_session.py    # TeachingSessionModel
│   ├── session_memory.py      # SessionMemoryModel
│   ├── teacher_memory.py      # TeacherMemoryModel
│   └── message.py              # MessageModel
├── agents/              # AI 智能体实现
│   ├── tools/           # 智能体工具
│   ├── teacher_agent.py # 教师 agent
│   └── student_agent.py # 学生 agent
├── configs/             # 配置文件（YAML）
│   ├── llm.yml          # LLM 配置
│   ├── app.yml          # 应用配置
│   ├── database.yml     # 数据库配置
│   └── chroma.yml       # 向量数据库配置
├── datas/               # 数据文件（数据库、向量数据库等）
├── core/                # 核心业务逻辑
├── dependencies/        # 依赖注入配置
├── middlewares/         # 自定义中间件
├── schemas/             # Pydantic 数据模型（API验证）
├── services/           # 业务服务
├── tests/               # 测试文件
├── main.py              # 应用入口
├── .env.example         # 环境变量模板
├── pyproject.toml       # Ruff 配置
└── requirements.txt     # Python 依赖
```

**目录说明**:
- **models/**: 功能模块，每个功能包含 router（路由）和 service（业务逻辑）
- **orm/**: 数据库ORM模型，与SQLAlchemy对应的表定义
- **分离原因**: 避免ORM模型和业务模块混在一起，职责清晰

## 环境配置

### 1. 环境变量

复制 `.env.example` 为 `.env` 并填写 API 密钥：

```bash
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key
```

### 2. YAML 配置文件

配置文件位于 `configs/` 目录，按功能分类：

| 文件 | 说明 |
|------|------|
| `configs/llm.yml` | LLM 配置（模型、API 地址、参数） |
| `configs/app.yml` | 应用配置（端口、CORS 等） |
| `configs/database.yml` | 数据库连接池配置（pool_size、max_overflow） |
| `configs/chroma.yml` | 向量数据库配置 |

### 3. 数据库配置

项目使用 **PostgreSQL** 作为主数据库，连接信息通过环境变量配置。

**`.env` 配置**（必须）：

```bash
DATABASE_URL=postgresql+asyncpg://admin:123456@localhost:5432/teaching_agent_db
```

**`configs/database.yml`**（连接池参数，可选）：

```yaml
database:
  pool_size: 5
  max_overflow: 10
```

**数据库名统一规则**：`.env` 中的 `DATABASE_URL` 是唯一的连接信息来源。`alembic.ini` 中的 URL 仅作为 fallback，Alembic 运行时会优先读取 `.env` 中的 `DATABASE_URL` 并自动将 `+asyncpg` 转换为 `+psycopg2`（Alembic 使用同步驱动执行迁移）。

**修改 LLM 模型：** 编辑 `configs/llm.yml`
```yaml
llm:
  model: Qwen/Qwen2.5-72B-Instruct  # 修改为其他模型
  temperature: 0.7
  max_tokens: 2000
```

**支持的 LLM 提供商：**
- 硅基流动（默认）：使用免费的 Qwen2.5-7B-Instruct 模型
- OpenAI：修改 `configs/llm.yml` 中的 `base_url`

**其他可用模型（硅基流动）：**
- `Qwen/Qwen2.5-7B-Instruct` - 免费，轻量级
- `Qwen/Qwen2.5-72B-Instruct` - 免费，更强性能
- `deepseek-ai/DeepSeek-V3` - 深度求索模型
- `THUDM/glm-4-9b-chat` - 智谱 GLM-4

## 开发命令

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的硅基流动 API Key（或其他兼容 OpenAI 格式的 API Key）

# 启动开发服务器 (http://0.0.0.0:8000)
python main.py

# 代码检查
ruff check .              # 检查代码问题
ruff check . --fix        # 自动修复问题

# 代码格式化
ruff format .             # 格式化代码
ruff format . --check     # 检查格式（不修改）

# 访问 API 文档
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## API 文档

### 实时文档（开发调试用）
- **Swagger UI**: http://localhost:8000/docs - 可直接测试接口
- **ReDoc**: http://localhost:8000/redoc - 只读文档

### 静态文档（详细说明）
- 完整 API 文档位于 [docs/api.md](../docs/api.md)
- 每次新增接口后请更新该文档

### 添加新接口时
1. 在 FastAPI 路由中编写接口（会自动出现在 Swagger UI）
2. 更新 `docs/api.md` 文档，添加详细说明
3. 在路由函数的 docstring 中添加描述（会显示在 Swagger UI）

## 数据库迁移 (Alembic)

项目使用 Alembic 进行数据库版本控制和迁移管理。

### 前置条件

1. PostgreSQL 服务已启动（本项目使用 Docker: `postgres:15`）
2. `.env` 中已配置 `DATABASE_URL`

### 首次设置

首次运行项目时，需要创建数据库表结构：

```bash
# 创建数据库（如果不存在）
docker exec pg-service-15 psql -U admin -c "CREATE DATABASE teaching_agent_db;"

# 初始化数据库（创建所有表）
alembic upgrade head
```

执行后会创建以下表：
- `teaching_sessions` - 教学会话表
- `session_memories` - 会话记忆表
- `teacher_memories` - 教师记忆表
- `student_memories` - 学生记忆表
- `messages` - 消息表
- `checkpoint_plans` - 检查点计划表
- `alembic_version` - Alembic 版本控制表

### 创建新迁移

当修改了 ORM 模型（`orm/` 目录下的文件）后，需要创建新的迁移脚本：

```bash
# 自动生成迁移脚本（推荐）
alembic revision --autogenerate -m "描述变更内容"

# 示例：
# alembic revision --autogenerate -m "添加用户头像字段"
# alembic revision --autogenerate -m "创建订单表"
```

**注意事项：**
- `--autogenerate` 会自动检测 ORM 模型的变化
- 生成的迁移脚本位于 `alembic/versions/` 目录
- 生成后请检查迁移脚本内容是否正确
- 提交代码时包含迁移脚本

### 应用迁移

将待执行的迁移应用到数据库：

```bash
# 应用所有待执行的迁移
alembic upgrade head

# 应用到指定版本
alembic upgrade <revision_id>

# 示例：
# alembic upgrade 2c224e826c17
```

### 回滚迁移

回滚到之前的迁移版本：

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>

# 回滚到初始状态（删除所有表）
alembic downgrade base
```

**警告：** 回滚会删除数据，请谨慎操作！

### 查看迁移状态

```bash
# 查看当前数据库版本
alembic current

# 查看所有迁移历史
alembic history

# 查看待执行的迁移
alembic heads
```

### 迁移脚本示例

生成的迁移脚本位于 `alembic/versions/` 目录：

```
alembic/versions/
├── 2c224e826c17_创建初始表结构.py       # 初始迁移
├── a1b2c3d4e5f6_添加用户头像字段.py     # 后续迁移示例
└── ...
```

### 外键约束说明

PostgreSQL 默认启用外键约束，所有包含 `session_id` 的表都通过 `ForeignKeyConstraint` 关联到 `teaching_sessions` 表，支持级联删除。

### 数据库连接配置

- **连接信息**: `.env` 中的 `DATABASE_URL`（唯一来源）
- **连接池**: `configs/database.yml`（pool_size、max_overflow）
- **迁移配置**: `alembic.ini`（fallback，优先使用 .env）
- **环境配置**: `alembic/env.py`（自动加载 .env，asyncpg→psycopg2 转换）

### 迁移最佳实践

1. **先 autogenerate，后检查**: 使用 `--autogenerate` 后务必检查生成的脚本
2. **小步快跑**: 每次修改 ORM 后立即创建迁移，不要积累太多变更
3. **测试迁移**: 在开发环境测试迁移后再部署到生产环境
4. **备份重要数据**: 执行迁移前备份重要数据
5. **版本控制**: 将迁移脚本纳入版本控制，便于团队协作
