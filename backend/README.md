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

复制 `.env.example` 为 `.env` 并填写相关配置：

```bash
cp .env.example .env
```

`.env` 配置项说明：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | LLM API 密钥（硅基流动/ OpenAI） | - |
| `OPENAI_BASE_URL` | LLM API 地址 | https://api.siliconflow.cn/v1 |
| `OPENAI_MODEL` | 使用的模型名称 | Qwen/Qwen2.5-7B-Instruct（免费） |
| `APP_HOST` | 服务监听地址 | 0.0.0.0 |
| `APP_PORT` | 服务监听端口 | 8000 |
| `DEBUG` | 调试模式 | True |
| `DATABASE_URL` | 数据库连接地址 | sqlite+aiosqlite:///./database.db |
| `CHROMA_PERSIST_DIR` | ChromaDB 持久化目录 | ./chroma_db |

**支持的 LLM 提供商：**
- 硅基流动（默认）：兼容 OpenAI SDK，使用免费的 Qwen2.5-7B-Instruct 模型
- OpenAI：修改 `OPENAI_BASE_URL` 为 `https://api.openai.com/v1`

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
