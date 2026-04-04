# Alembic 数据库迁移脚本实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为教学智能体项目配置 Alembic 并创建初始数据库迁移脚本，将 ORM 模型同步到数据库表结构。

**Architecture:** 使用 Alembic 作为 SQLAlchemy 的迁移工具。通过 `alembic revision --autogenerate` 自动生成迁移脚本，然后手动优化确保正确性。数据库文件位于 `backend/datas/database.db`。

**Tech Stack:** Alembic 1.18.4, SQLAlchemy 2.x, SQLite (async)

---

## 文件结构

```
backend/
├── alembic/                          # 新建目录
│   ├── versions/                     # 迁移脚本目录
│   │   └── 001_initial_tables.py     # 初始表迁移
│   ├── env.py                        # Alembic 环境配置
│   ├── script.py                     # Alembic 命令行脚本
│   └── alembic.ini                   # Alembic 配置文件
├── core/
│   └── database.py                   # 已存在 - Base 类定义
├── orm/                              # 已存在的 ORM 模型
│   ├── teaching_session.py
│   ├── session_memory.py
│   ├── message.py
│   └── teacher_memory.py
└── datas/
    └── database.db                   # SQLite 数据库文件（迁移后创建）
```

---

## Task 1: 初始化 Alembic

**目标:** 在项目中创建 Alembic 基础目录结构和配置文件。

**Files:**
- Create: `backend/alembic/`
- Create: `backend/alembic.ini`
- Modify: `backend/alembic/env.py` (自动生成后需修改)

- [ ] **Step 1: 运行 alembic init 命令**

```bash
cd backend
alembic init alembic
```

Expected: 创建 `alembic/` 目录和 `alembic.ini` 文件

- [ ] **Step 2: 验证目录结构创建成功**

```bash
ls -la alembic/
```

Expected: 看到 `versions/` 目录和 `env.py` 文件

- [ ] **Step 3: 提交初始化文件**

```bash
git add backend/alembic/ backend/alembic.ini
git commit -m "feat: 初始化 Alembic 迁移工具"
```

---

## Task 2: 配置 alembic.ini

**目标:** 配置 Alembic 使用项目的数据库连接字符串。

**Files:**
- Modify: `backend/alembic.ini`

- [ ] **Step 1: 读取当前 alembic.ini**

```bash
cat backend/alembic.ini | grep sqlalchemy.url
```

- [ ] **Step 2: 修改数据库 URL**

找到 `sqlalchemy.url = driver://user:pass@localhost/dbname` 这一行，修改为：

```ini
sqlalchemy.url = sqlite+aiosqlite:///datas/database.db
```

**说明:** 使用 `sqlite+aiosqlite:///` 前缀支持异步操作，数据库路径相对于项目根目录的 `datas/` 目录。

- [ ] **Step 3: 提交配置更改**

```bash
git add backend/alembic.ini
git commit -m "config: 设置 Alembic 数据库 URL 为 SQLite"
```

---

## Task 3: 配置 env.py 支持异步和 ORM 模型导入

**目标:** 修改 Alembic 环境配置以支持异步数据库连接和自动发现 ORM 模型。

**Files:**
- Modify: `backend/alembic/env.py`

- [ ] **Step 1: 读取当前 env.py 内容**

```bash
cat backend/alembic/env.py
```

- [ ] **Step 2: 替换 env.py 的导入和配置部分**

将文件开头部分替换为以下内容：

```python
"""Alembic 环境配置."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入 ORM Base 和模型
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.database import Base
from orm.message import MessageModel
from orm.session_memory import SessionMemoryModel
from orm.teacher_memory import TeacherMemoryModel
from orm.teaching_session import TeachingSessionModel

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata
```

- [ ] **Step 3: 替换 run_migrations_online 函数为异步版本**

找到 `def run_migrations_online()` 函数，替换为：

```python
def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def run_async_migrations() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations, connection)

    asyncio.run(run_async_migrations())
```

- [ ] **Step 4: 提交 env.py 更改**

```bash
git add backend/alembic/env.py
git commit -m "config: 配置 Alembic 支持异步和 ORM 模型自动发现"
```

---

## Task 4: 创建初始迁移脚本（autogenerate）

**目标:** 使用 Alembic 自动生成功能创建初始表结构迁移脚本。

**Files:**
- Create: `backend/alembic/versions/001_initial_tables.py`

- [ ] **Step 1: 运行 autogenerate 命令**

```bash
cd backend
alembic revision --autogenerate -m "创建初始表结构"
```

Expected: 在 `alembic/versions/` 目录下创建新的迁移文件

- [ ] **Step 2: 检查生成的迁移文件名**

```bash
ls -lt backend/alembic/versions/ | head -5
```

Expected: 看到类似 `001_xxxxx_create_initial_tables.py` 的文件

- [ ] **Step 3: 暂不提交，先验证迁移脚本内容**

```bash
cat backend/alembic/versions/001_*.py
```

---

## Task 5: 验证并优化迁移脚本

**目标:** 检查自动生成的迁移脚本是否正确，手动优化不合理的地方。

**Files:**
- Modify: `backend/alembic/versions/001_*.py`

- [ ] **Step 1: 检查 upgrade() 函数内容**

迁移文件应包含以下表的定义：

1. `teaching_sessions` 表
2. `session_memories` 表
3. `teacher_memories` 表
4. `messages` 表

验证每个表的列定义是否与 ORM 模型一致。

- [ ] **Step 2: 检查外键约束**

确认以下外键正确创建：
- `session_memories.session_id` → `teaching_sessions.id`
- `messages.session_id` → `teaching_sessions.id`
- `teacher_memories.session_id` → `teaching_sessions.id`

- [ ] **Step 3: 检查索引和外键命名**

Alembic 自动生成的命名通常合理，但确认无冲突。

- [ ] **Step 4: 如有问题手动修正**

如果 autogenerate 没有正确识别某些字段，手动添加。例如，如果 JSON 类型没有正确识别：

```python
# 在 upgrade() 中确保使用 JSON 类型
sa.Column('students_config', sa.JSON(), nullable=False),
sa.Column('message_history', sa.JSON(), nullable=False),
```

- [ ] **Step 5: 提交迁移脚本**

```bash
git add backend/alembic/versions/001_*.py
git commit -m "feat: 添加初始数据库表结构迁移脚本"
```

---

## Task 6: 执行迁移创建数据库表

**目标:** 运行迁移脚本在数据库中创建表结构。

**Files:**
- Create: `backend/datas/database.db` (自动创建)

- [ ] **Step 1: 确保 datas 目录存在**

```bash
mkdir -p backend/datas
```

- [ ] **Step 2: 执行数据库升级**

```bash
cd backend
alembic upgrade head
```

Expected: 看到 "Running upgrade -> " 的输出信息

- [ ] **Step 3: 验证数据库文件已创建**

```bash
ls -la backend/datas/database.db
```

Expected: 看到database.db 文件

- [ ] **Step 4: 使用 SQLite 命令验证表结构**

```bash
sqlite3 backend/datas/database.db ".tables"
```

Expected: 看到以下表：
- `teaching_sessions`
- `session_memories`
- `teacher_memories`
- `messages`
- `alembic_version` (Alembic 版本控制表)

- [ ] **Step 5: 检查 teaching_sessions 表结构**

```bash
sqlite3 backend/datas/database.db ".schema teaching_sessions"
```

Expected: 看到包含 id, teaching_mode, topic, students_config, duration_seconds, status, start_time, end_time 列的 CREATE TABLE 语句

- [ ] **Step 6: 提交数据库文件**

```bash
git add backend/datas/database.db
git commit -m "chore: 初始化数据库表结构"
```

---

## Task 7: 编写迁移测试

**目标:** 创建测试验证迁移脚本正确性。

**Files:**
- Create: `backend/tests/test_alembic_migration.py`

- [ ] **Step 1: 创建测试文件**

创建 `backend/tests/test_alembic_migration.py`:

```python
"""Alembic 迁移测试."""

import pytest
import sqlite3
from pathlib import Path


class TestAlembicMigration:
    """测试 Alembic 迁移是否正确执行."""

    @pytest.fixture
    def db_path(self):
        """获取数据库文件路径."""
        return Path(__file__).parents[1] / "datas" / "database.db"

    def test_database_file_exists(self, db_path):
        """测试数据库文件是否存在."""
        assert db_path.exists(), "数据库文件不存在"

    def test_all_tables_exist(self, db_path):
        """测试所有表是否已创建."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        conn.close()

        expected_tables = {
            "teaching_sessions",
            "session_memories",
            "teacher_memories",
            "messages",
            "alembic_version",
        }

        assert expected_tables.issubset(tables), f"缺少表: {expected_tables - tables}"

    def test_teaching_sessions_columns(self, db_path):
        """测试 teaching_sessions 表列是否正确."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(teaching_sessions)")
        columns = {row[1] for row in cursor.fetchall()}

        conn.close()

        expected_columns = {
            "id", "teaching_mode", "topic", "students_config",
            "duration_seconds", "status", "start_time", "end_time"
        }

        assert expected_columns == columns, f"列不匹配: 期望 {expected_columns}, 实际 {columns}"

    def test_foreign_keys_exist(self, db_path):
        """测试外键约束是否存在."""
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]

        conn.close()

        assert fk_enabled == 1, "外键约束未启用"
```

- [ ] **Step 2: 运行测试**

```bash
cd backend
pytest tests/test_alembic_migration.py -v
```

Expected: 所有测试通过

- [ ] **Step 3: 提交测试文件**

```bash
git add backend/tests/test_alembic_migration.py
git commit -m "test: 添加 Alembic 迁移测试"
```

---

## Task 8: 创建 alembic.ini.example 作为配置模板

**目标:** 提供配置模板供其他开发者参考。

**Files:**
- Create: `backend/alembic.ini.example`

- [ ] **Step 1: 复制 alembic.ini 作为模板**

```bash
cp backend/alembic.ini backend/alembic.ini.example
```

- [ ] **Step 2: 在文件顶部添加说明注释**

编辑 `backend/alembic.ini.example`，在开头添加：

```ini
# Alembic 配置文件示例
# 复制此文件为 alembic.ini 并根据需要修改
# 主要修改 sqlalchemy.url 为你的数据库连接字符串
```

- [ ] **Step 3: 更新 .gitignore**

确保 `backend/.gitignore` 包含：

```
# Alembic
alembic.ini
datas/*.db
datas/*.db-journal
```

- [ ] **Step 4: 提交模板和 gitignore 更改**

```bash
git add backend/alembic.ini.example backend/.gitignore
git commit -m "docs: 添加 Alembic 配置模板和更新 gitignore"
```

---

## Task 9: 编写迁移使用文档

**目标:** 在测试文档中添加 Alembic 使用说明。

**Files:**
- Modify: `docs/tests/backend/index.md`

- [ ] **Step 1: 在 backend 测试文档中添加 Alembic 章节**

在 `docs/tests/backend/index.md` 末尾添加：

```markdown
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

### 查看迁移历史

查看已应用的迁移版本：

```bash
alembic history
```

查看当前版本：

```bash
alembic current
```
```

- [ ] **Step 2: 提交文档更新**

```bash
git add docs/tests/backend/index.md
git commit -m "docs: 添加 Alembic 迁移使用文档"
```

---

## Task 10: 验证完整迁移流程

**目标:** 从零开始验证完整迁移流程。

**Files:**
- Test: 所有迁移相关文件

- [ ] **Step 1: 备份当前数据库**

```bash
cp backend/datas/database.db backend/datas/database.db.backup
```

- [ ] **Step 2: 删除数据库和 alembic 版本**

```bash
rm backend/datas/database.db
```

- [ ] **Step 3: 重新运行迁移**

```bash
cd backend
alembic upgrade head
```

- [ ] **Step 4: 运行所有测试验证**

```bash
pytest tests/ -v
```

Expected: 所有测试通过（包括原有的 ORM 测试和新的迁移测试）

- [ ] **Step 5: 检查 Alembic 版本**

```bash
sqlite3 backend/datas/database.db "SELECT version_num FROM alembic_version"
```

Expected: 看到版本号（如 '001' 或迁移文件的 revision id）

- [ ] **Step 6: 清理备份文件**

```bash
rm backend/datas/database.db.backup
```

- [ ] **Step 7: 最终提交所有更改**

```bash
git add -A
git commit -m "chore: 完成 Alembic 迁移配置，验证通过"
```

---

## 验收标准

完成所有任务后：

- [ ] `alembic/` 目录结构完整
- [ ] `alembic.ini` 配置正确
- [ ] `alembic/env.py` 支持异步和 ORM 模型导入
- [ ] 迁移脚本 `001_initial_tables.py` 正确创建 4 张表
- [ ] 数据库文件 `datas/database.db` 已创建
- [ ] 运行 `alembic history` 看到迁移历史
- [ ] 运行 `pytest tests/` 所有测试通过
- [ ] 文档已更新 Alembic 使用说明

---

## 故障排查

### 问题: alembic 命令找不到

```bash
# 解决方案: 确保 alembic 已安装
pip install alembic
# 或重新安装项目依赖
pip install -r requirements.txt
```

### 问题: autogenerate 没有检测到模型变更

```bash
# 检查 env.py 中的 target_metadata 是否设置为 Base.metadata
# 确保所有 ORM 模型已导入并可以访问 Base
```

### 问题: 外键约束在 SQLite 中不生效

```bash
# SQLite 需要显式启用外键约束
# 在每次连接时执行: PRAGMA foreign_keys = ON;
# 或者在 alembic/env.py 中配置
```

### 问题: 迁移脚本生成后无法执行

```bash
# 检查生成的 SQL 语法
alembic upgrade head --sql
# 查看即将执行的 SQL，手动验证
```

---

## 下一步

迁移系统配置完成后，可以继续：
- Phase 2: 学生创建系统
- Phase 3: Memory 系统
- Phase 4: 教师 Agent

每次修改 ORM 模型后，记得运行：
```bash
alembic revision --autogenerate -m "描述变更"
alembic upgrade head
```
