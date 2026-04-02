# 教学智能体 - 后端

基于 FastAPI + LangChain 构建的教学智能体系统后端。

## 技术栈

- **FastAPI** - 高性能 Web 框架
- **LangChain** - AI/LLM 应用开发框架
- **硅基流动 / OpenAI SDK** - 大语言模型接口（兼容 OpenAI 格式）
- **ChromaDB** - 向量数据库（用于 RAG、知识库）
- **SQLAlchemy** - ORM 数据库操作
- **Alembic** - 数据库迁移工具
- **Uvicorn** - ASGI 服务器

## 目录结构

```
backend/
├── agents/         # AI 智能体实现
│   └── tools/      # 智能体会用到的工具
├── configs/        # 需要用到的相关的配置项
├── core/           # 核心业务逻辑
├── dependencies/   # 依赖注入配置
├── middlewares/    # 自定义中间件
├── routers/        # API 路由
├── tests/          # 测试文件
├── main.py         # 应用入口
└── requirements.txt # Python 依赖
```

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
| `configs/database.yml` | 数据库配置 |
| `configs/chroma.yml` | 向量数据库配置 |

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
