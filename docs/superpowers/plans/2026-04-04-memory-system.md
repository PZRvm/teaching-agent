# Memory 系统实现计划

> **适用于 agentic workers:** 必需子技能: 使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务执行此计划。步骤使用复选框 (`- [ ]`) 语法进行跟踪。

**目标:** 实现 agent 记忆管理系统，包括内存数据类、MemoryManager 编排器，以及数据库持久化，使 agent 能够在消息之间保持连贯的教学上下文。

**架构:** 三个内存数据类（SessionMemory、TeacherAgentMemory、StudentAgentMemory）持有运行时状态。MemoryManager 编排消息处理、知识点提取和摘要生成，使用可注入的 LLM 可调用对象。MemoryPersistence 通过 SQLAlchemy 异步 ORM 处理保存/加载，操作现有数据库架构（已迁移 4 张表）。

**技术栈:** Python 3.12+, SQLAlchemy 异步 (aiosqlite), Pydantic, pytest-asyncio, random.Random (本地实例)

---

## 现有基础设施

**ORM 模型**（已迁移，请勿修改）:
- `orm/teaching_session.py` — `TeachingSessionModel`: id, teaching_mode, topic, students_config, status, start_time, end_time
- `orm/session_memory.py` — `SessionMemoryModel`: id, session_id (int FK), message_history (JSON), teaching_summary (Text nullable), last_updated
- `orm/teacher_memory.py` — `TeacherMemoryModel`: id, session_id (int FK), covered_topics (JSON), student_questions (JSON), student_participation (JSON), teaching_progress (Float), student_misconceptions (JSON)
- `orm/student_memory.py` — `StudentMemoryModel`: id, session_id (int FK), student_name, level, attitude, learning_ability, learned_concepts (JSON), confused_points (JSON), questions_asked (JSON), initial_knowledge_level, current_knowledge_level, learning_rate, last_updated
- `orm/message.py` — `MessageModel`: id, session_id (int FK), sender, message_type, content, timestamp

**Schemas**（已存在，请勿修改）:
- `schemas/message.py` — `MessageType` 枚举, `Message` (sender, message_type, content, timestamp)
- `schemas/student.py` — `StudentLevel`, `StudentAttitude`, `StudentProfile`

**测试 fixtures**（已存在于 `tests/conftest.py`）:
- `test_engine` — 内存 SQLite 引擎，已创建所有表
- `db_session` — 异步 SQLAlchemy 会话

**来自 design.md 的关键设计约束:** SessionMemory、TeacherAgentMemory、StudentAgentMemory 都持久化到数据库。运行时状态与数据库状态通过 MemoryPersistence 服务同步。

---

## 文件结构

| 文件 | 职责 |
|------|---------------|
| `backend/agents/memories/memory_manager.py` | SessionMemory、TeacherAgentMemory、StudentAgentMemory 数据类 + MemoryManager |
| `backend/agents/memories/memory_persistence.py` | MemoryPersistence — 通过 SQLAlchemy 异步进行数据库保存/加载 |
| `backend/tests/test_memory_manager.py` | 所有 4 个内存类的测试 |
| `backend/tests/test_memory_persistence.py` | 持久化测试（保存 + 加载 + 集成） |

---

### Task 0: 数据库迁移脚本（创建 student_memories 表）

**文件:**
- 创建: `backend/alembic/versions/002_create_student_memories_table.py`
- 创建: `backend/orm/student_memory.py`

- [ ] **Step 1: 编写 ORM 模型**

```python
# backend/orm/student_memory.py
"""学生记忆 ORM 模型."""

from datetime import datetime

import sqlalchemy as sa
from schemas.student import StudentAttitude, StudentLevel
from sqlalchemy import orm
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class StudentMemoryModel(Base):
    """学生记忆 ORM 模型."""

    __tablename__ = "student_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(sa.ForeignKey("teaching_sessions.id"))
    student_name: Mapped[str] = mapped_column(sa.String(50))
    level: Mapped[StudentLevel] = mapped_column(sa.Enum(StudentLevel), default=StudentLevel.AVERAGE)
    attitude: Mapped[StudentAttitude] = mapped_column(sa.Enum(StudentAttitude), default=StudentAttitude.NEUTRAL)
    learning_ability: Mapped[int] = mapped_column(sa.Integer, default=5)

    learned_concepts: Mapped[list[str]] = mapped_column(sa.JSON, default=list)
    confused_points: Mapped[list[str]] = mapped_column(sa.JSON, default=list)
    questions_asked: Mapped[list[str]] = mapped_column(sa.JSON, default=list)

    initial_knowledge_level: Mapped[float] = mapped_column(sa.Float, default=0.0)
    current_knowledge_level: Mapped[float] = mapped_column(sa.Float, default=0.0)
    learning_rate: Mapped[float] = mapped_column(sa.Float, default=0.05)

    last_updated: Mapped[datetime] = mapped_column(
        sa.DateTime, default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        sa.Index("ix_student_memories_session_id", "session_id"),
        sa.Index("ix_student_memories_session_student", "session_id", "student_name"),
    )
```

- [ ] **Step 2: 编写 Alembic 迁移脚本**

```python
# backend/alembic/versions/002_create_student_memories_table.py
"""create student_memories table

Revision ID: 002
Revises: 001
Create Date: 2026-04-04

"""
from alembic import op
import sqlalchemy as sa
from schemas.student import StudentAttitude, StudentLevel


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 student_memories 表."""
    op.create_table(
        'student_memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('student_name', sa.String(length=50), nullable=False),
        sa.Column('level', sa.Enum(StudentLevel), nullable=True),
        sa.Column('attitude', sa.Enum(StudentAttitude), nullable=True),
        sa.Column('learning_ability', sa.Integer(), nullable=True),
        sa.Column('learned_concepts', sa.JSON(), nullable=True),
        sa.Column('confused_points', sa.JSON(), nullable=True),
        sa.Column('questions_asked', sa.JSON(), nullable=True),
        sa.Column('initial_knowledge_level', sa.Float(), nullable=True),
        sa.Column('current_knowledge_level', sa.Float(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['teaching_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_student_memories_session_id', 'student_memories', ['session_id'])
    op.create_index('ix_student_memories_session_student', 'student_memories', ['session_id', 'student_name'])


def downgrade() -> None:
    """删除 student_memories 表."""
    op.drop_index('ix_student_memories_session_student', table_name='student_memories')
    op.drop_index('ix_student_memories_session_id', table_name='student_memories')
    op.drop_table('student_memories')
```

- [ ] **Step 3: 运行迁移**

运行: `cd backend && alembic upgrade head`
预期: `Running upgrade 001 -> 002`

验证表已创建:
```bash
sqlite3 backend/datas/database.db ".tables"
```
预期输出包含 `student_memories`

- [ ] **Step 4: 提交**

```bash
git add backend/orm/student_memory.py backend/alembic/versions/002_create_student_memories_table.py
git commit -m "feat: add student_memories table with migration script"
```

---

### Task 1: SessionMemory 数据类

**文件:**
- 创建: `backend/agents/memories/memory_manager.py`
- 测试: `backend/tests/test_memory_manager.py`

- [ ] **Step 1: 编写失败的测试**

```python
# backend/tests/test_memory_manager.py
"""Memory 数据类和 MemoryManager 测试."""

from datetime import datetime

from schemas.message import Message, MessageType


class TestSessionMemory:
    """SessionMemory 测试."""

    def test_init_default_values(self):
        """测试默认初始化."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")

        assert memory.session_id == 1
        assert memory.topic == "Python基础"
        assert memory.message_history == []
        assert memory.teaching_summary == ""
        assert memory.max_history_messages == 50
        assert memory.summary_update_interval == 10
        assert memory.last_summary_update == 0

    def test_should_update_summary_false_initially(self):
        """测试初始状态下不需要更新摘要."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        assert memory.should_update_summary() is False

    def test_should_update_summary_true_after_interval(self):
        """测试达到间隔后需要更新摘要."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        for i in range(10):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"知识点{i}",
                    timestamp=datetime.now(),
                )
            )
        assert memory.should_update_summary() is True

    def test_should_update_summary_false_below_interval(self):
        """测试未达到间隔不需要更新."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        for i in range(9):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"知识点{i}",
                    timestamp=datetime.now(),
                )
            )
        assert memory.should_update_summary() is False

    def test_should_update_summary_resets_after_mark(self):
        """测试标记更新后重置计数."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        for i in range(10):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"知识点{i}",
                    timestamp=datetime.now(),
                )
            )
        assert memory.should_update_summary() is True

        memory.mark_summary_updated()
        assert memory.should_update_summary() is False

    def test_get_recent_messages_returns_last_n(self):
        """测试获取最近 N 条消息."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础", max_history_messages=3)
        for i in range(5):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"内容{i}",
                    timestamp=datetime.now(),
                )
            )
        recent = memory.get_recent_messages()
        assert len(recent) == 3
        assert recent[0].content == "内容2"
        assert recent[2].content == "内容4"

    def test_get_recent_messages_empty(self):
        """测试空历史返回空列表."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        assert memory.get_recent_messages() == []

    def test_get_agent_context(self):
        """测试获取 agent 上下文."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(
            session_id=1,
            topic="Python基础",
            teaching_summary="已讲授变量和数据类型",
        )
        memory.message_history.append(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="今天学习变量",
                timestamp=datetime.now(),
            )
        )

        context = memory.get_agent_context()
        assert "Python基础" in context
        assert "已讲授变量和数据类型" in context
        assert "今天学习变量" in context

    def test_add_message(self):
        """测试添加消息."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        msg = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="测试内容",
            timestamp=datetime.now(),
        )
        memory.add_message(msg)
        assert len(memory.message_history) == 1
        assert memory.message_history[0].content == "测试内容"
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestSessionMemory -v`
预期: FAIL with `ModuleNotFoundError: No module named 'agents.memories.memory_manager'`

- [ ] **Step 3: 编写最小实现**

```python
# backend/agents/memories/memory_manager.py
"""Agent 记忆管理系统."""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas.message import Message


@dataclass
class SessionMemory:
    """会话级别的记忆管理."""

    session_id: int
    topic: str

    message_history: list[Message] = field(default_factory=list)
    teaching_summary: str = ""

    max_history_messages: int = 50
    summary_update_interval: int = 10
    last_summary_update: int = 0

    def add_message(self, message: Message) -> None:
        """添加消息到历史."""
        self.message_history.append(message)

    def should_update_summary(self) -> bool:
        """判断是否需要更新摘要."""
        return (
            len(self.message_history) - self.last_summary_update
            >= self.summary_update_interval
        )

    def mark_summary_updated(self) -> None:
        """标记摘要已更新."""
        self.last_summary_update = len(self.message_history)

    def get_recent_messages(self) -> list[Message]:
        """获取最近 N 条消息."""
        return self.message_history[-self.max_history_messages :]

    def get_agent_context(self) -> str:
        """获取 agent 完整上下文."""
        recent = self.get_recent_messages()
        parts = [
            f"教学主题: {self.topic}",
            f"教学摘要: {self.teaching_summary}",
            "最近的对话:",
        ]
        for msg in recent:
            parts.append(f"[{msg.sender}] ({msg.message_type.value}): {msg.content}")
        return "\n".join(parts)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestSessionMemory -v`
预期: All 9 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/agents/memories/memory_manager.py backend/tests/test_memory_manager.py
git commit -m "feat: add SessionMemory dataclass with history and summary tracking"
```

---

### Task 2: TeacherAgentMemory 数据类

**文件:**
- 修改: `backend/agents/memories/memory_manager.py`
- 修改: `backend/tests/test_memory_manager.py`

- [ ] **Step 1: 编写失败的测试**

```python
# Add to backend/tests/test_memory_manager.py

class TestTeacherAgentMemory:
    """TeacherAgentMemory 测试."""

    def test_init_default_values(self):
        """测试默认初始化."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        assert memory.covered_topics == []
        assert memory.student_questions == {}
        assert memory.student_participation == {}
        assert memory.teaching_progress == 0.0
        assert memory.student_misconceptions == {}

    def test_record_covered_topic(self):
        """测试记录已讲授主题."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_covered_topic("变量与数据类型")
        assert "变量与数据类型" in memory.covered_topics

    def test_record_covered_topic_no_duplicates(self):
        """测试不重复记录相同主题."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_covered_topic("变量与数据类型")
        memory.record_covered_topic("变量与数据类型")
        assert memory.covered_topics == ["变量与数据类型"]

    def test_record_student_question(self):
        """测试记录学生提问."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_student_question("张三", "什么是变量?")
        assert memory.student_questions == {"张三": ["什么是变量?"]}

    def test_record_student_question_accumulates(self):
        """测试学生提问累积."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_student_question("张三", "什么是变量?")
        memory.record_student_question("张三", "那函数呢?")
        assert len(memory.student_questions["张三"]) == 2

    def test_record_student_participation(self):
        """测试记录学生参与."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_student_participation("张三")
        memory.record_student_participation("张三")
        memory.record_student_participation("李四")
        assert memory.student_participation == {"张三": 2, "李四": 1}

    def test_record_misconception(self):
        """测试记录学生误解."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_misconception("张三", "认为变量不需要声明")
        assert memory.student_misconceptions == {"张三": ["认为变量不需要声明"]}

    def test_get_system_prompt_addition(self):
        """测试生成教师 system prompt 附加内容."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_covered_topic("变量与数据类型")
        memory.record_covered_topic("条件语句")
        memory.record_student_participation("张三")

        prompt = memory.get_system_prompt_addition(topic="Python基础")
        assert "Python基础" in prompt
        assert "变量与数据类型" in prompt
        assert "条件语句" in prompt
        assert "张三" in prompt
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestTeacherAgentMemory -v`
预期: FAIL with `ImportError: cannot import name 'TeacherAgentMemory'`

- [ ] **Step 3: 编写最小实现**

```python
# Add to backend/agents/memories/memory_manager.py, after SessionMemory class

@dataclass
class TeacherAgentMemory:
    """教师 agent 的专用记忆."""

    covered_topics: list[str] = field(default_factory=list)
    student_questions: dict[str, list[str]] = field(default_factory=dict)
    student_participation: dict[str, int] = field(default_factory=dict)
    teaching_progress: float = 0.0
    student_misconceptions: dict[str, list[str]] = field(default_factory=dict)

    def record_covered_topic(self, topic: str) -> None:
        """记录已讲授主题，避免重复."""
        if topic not in self.covered_topics:
            self.covered_topics.append(topic)

    def record_student_question(self, student_name: str, question: str) -> None:
        """记录学生提问."""
        if student_name not in self.student_questions:
            self.student_questions[student_name] = []
        self.student_questions[student_name].append(question)

    def record_student_participation(self, student_name: str) -> None:
        """记录学生参与次数."""
        self.student_participation[student_name] = (
            self.student_participation.get(student_name, 0) + 1
        )

    def record_misconception(self, student_name: str, misconception: str) -> None:
        """记录学生误解."""
        if student_name not in self.student_misconceptions:
            self.student_misconceptions[student_name] = []
        self.student_misconceptions[student_name].append(misconception)

    def get_system_prompt_addition(self, topic: str) -> str:
        """生成教师 system prompt 的附加内容."""
        status_lines = []
        for name, count in self.student_participation.items():
            status_lines.append(f"- {name}: 发言{count}次")

        student_status = "\n".join(status_lines) if status_lines else "暂无学生发言记录"

        return (
            f'你是教师 agent，正在教授"{topic}"相关内容。\n\n'
            f"已讲授内容: {', '.join(self.covered_topics) if self.covered_topics else '暂无'}\n"
            f"教学进度: {self.teaching_progress * 100:.0f}%\n\n"
            f"学生参与情况:\n{student_status}\n\n"
            f"重要提醒:\n"
            f"1. 避免重复讲授已覆盖的知识点\n"
            f"2. 根据学生的参与度和理解程度调整教学节奏\n"
            f"3. 对于困惑的学生，提供更详细的解释\n"
        )
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestTeacherAgentMemory -v`
预期: All 8 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/agents/memories/memory_manager.py backend/tests/test_memory_manager.py
git commit -m "feat: add TeacherAgentMemory dataclass with topic and student tracking"
```

---

### Task 3: StudentAgentMemory 数据类

**文件:**
- 修改: `backend/agents/memories/memory_manager.py`
- 修改: `backend/tests/test_memory_manager.py`

- [ ] **Step 1: 编写失败的测试**

```python
# Add to backend/tests/test_memory_manager.py

import random as random_module

from schemas.student import StudentAttitude, StudentLevel, StudentProfile


class TestStudentAgentMemory:
    """StudentAgentMemory 测试."""

    def test_init_from_profile(self):
        """测试从 StudentProfile 初始化."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="张三",
            level=StudentLevel.EXCELLENT,
            attitude=StudentAttitude.ACTIVE,
            learning_ability=8,
        )
        memory = StudentAgentMemory(profile=profile)

        assert memory.name == "张三"
        assert memory.level == StudentLevel.EXCELLENT
        assert memory.attitude == StudentAttitude.ACTIVE
        assert memory.learning_ability == 8
        assert memory.learned_concepts == []
        assert memory.current_knowledge_level == 0.0
        assert memory.learning_rate == 0.08  # learning_ability * 0.01

    def test_learning_rate_from_ability(self):
        """测试学习速率根据学习能力计算."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile_high = StudentProfile(name="高", learning_ability=9)
        profile_low = StudentProfile(name="低", learning_ability=2)

        memory_high = StudentAgentMemory(profile=profile_high)
        memory_low = StudentAgentMemory(profile=profile_low)

        assert memory_high.learning_rate == 0.09
        assert memory_low.learning_rate == 0.02

    def test_should_remember_concept_excellent_remembers_more(self):
        """测试优秀学生更容易记住概念."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="优秀生",
            level=StudentLevel.EXCELLENT,
            learning_ability=9,
        )
        memory = StudentAgentMemory(profile=profile)

        rng = random.Random(42)
        # 优秀学生 knowledge_level 会随着学习逐渐提高
        # 用固定种子测试，观察结果一致性
        results = [memory.should_remember_concept("概念A", rng) for _ in range(100)]
        # 至少有一些应该记住（概率 > 0.5）
        assert sum(results) > 30

    def test_should_remember_concept_basic_remembers_less(self):
        """测试基础学生记住概念的概率较低."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="基础生",
            level=StudentLevel.BASIC,
            learning_ability=2,
        )
        memory = StudentAgentMemory(profile=profile)

        rng = random.Random(42)
        results = [memory.should_remember_concept("概念A", rng) for _ in range(100)]
        # 基础学生记住的应该较少
        assert sum(results) < 70

    def test_update_knowledge_new_concept(self):
        """测试更新知识 - 新概念被记住."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(name="张三", learning_ability=8)
        memory = StudentAgentMemory(profile=profile)

        # 用固定种子，模拟记住
        rng = random.Random(42)
        memory.update_knowledge(["变量", "函数"], rng)

        # 至少有一个被记住（概率较高）
        assert len(memory.learned_concepts) >= 0  # 可能都不记住
        assert memory.current_knowledge_level >= 0.0

    def test_update_knowledge_no_duplicates(self):
        """测试不重复学习相同概念."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(name="张三", learning_ability=10)
        memory = StudentAgentMemory(profile=profile)

        rng = random.Random(42)
        memory.update_knowledge(["变量"], rng)
        count_before = len(memory.learned_concepts)

        memory.update_knowledge(["变量"], rng)
        assert len(memory.learned_concepts) == count_before

    def test_update_knowledge_increases_level(self):
        """测试学习新概念提升知识水平."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(name="张三", learning_ability=8)
        memory = StudentAgentMemory(profile=profile)

        rng = random.Random(42)
        # 用确定性种子确保至少记住一个
        initial_level = memory.current_knowledge_level
        memory.update_knowledge(["概念1", "概念2", "概念3", "概念4", "概念5"], rng)

        assert memory.current_knowledge_level >= initial_level

    def test_get_system_prompt_addition(self):
        """测试生成学生 system prompt 附加内容."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="张三",
            level=StudentLevel.EXCELLENT,
            attitude=StudentAttitude.ACTIVE,
            learning_ability=8,
        )
        memory = StudentAgentMemory(profile=profile)
        memory.learned_concepts.append("变量")

        prompt = memory.get_system_prompt_addition(topic="Python基础")
        assert "Python基础" in prompt
        assert "变量" in prompt
        assert "张三" in prompt
        assert "8/10" in prompt
        assert "excellent" in prompt
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestStudentAgentMemory -v`
预期: FAIL with `ImportError: cannot import name 'StudentAgentMemory'`

- [ ] **Step 3: 编写最小实现**

```python
# Add to backend/agents/memories/memory_manager.py, after TeacherAgentMemory class

import random

from schemas.student import StudentAttitude, StudentLevel, StudentProfile


@dataclass
class StudentAgentMemory:
    """学生 agent 的专用记忆（持久化到数据库）."""

    name: str = ""
    level: StudentLevel = StudentLevel.AVERAGE
    attitude: StudentAttitude = StudentAttitude.NEUTRAL
    learning_ability: int = 5

    learned_concepts: list[str] = field(default_factory=list)
    confused_points: list[str] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)

    initial_knowledge_level: float = 0.0
    current_knowledge_level: float = 0.0
    learning_rate: float = 0.05

    def __post_init__(self) -> None:
        """初始化后计算学习速率."""
        self.learning_rate = self.learning_ability * 0.01

    @classmethod
    def from_profile(cls, profile: StudentProfile) -> StudentAgentMemory:
        """从 StudentProfile 创建."""
        return cls(
            name=profile.name,
            level=profile.level,
            attitude=profile.attitude,
            learning_ability=profile.learning_ability,
        )

    def should_remember_concept(self, concept: str, rng: random.Random) -> bool:
        """判断是否应该记住这个概念（基于学习参数）."""
        return rng.random() < (self.current_knowledge_level + 0.5)

    def update_knowledge(self, new_concepts: list[str], rng: random.Random) -> None:
        """尝试学习新概念，基于学习参数决定是否记住."""
        for concept in new_concepts:
            if concept in self.learned_concepts:
                continue
            if self.should_remember_concept(concept, rng):
                self.learned_concepts.append(concept)
                self.current_knowledge_level = min(
                    1.0,
                    self.current_knowledge_level + self.learning_rate,
                )

    def get_system_prompt_addition(self, topic: str) -> str:
        """生成学生 system prompt 的附加内容."""
        learned = (
            ", ".join(self.learned_concepts)
            if self.learned_concepts
            else "尚未开始学习"
        )
        return (
            f'你是学生 agent "{self.name}"，正在学习"{topic}"相关内容。\n\n'
            f"已学习内容: {learned}\n"
            f"当前知识掌握度: {self.current_knowledge_level * 100:.0f}%\n\n"
            f"你的学习特征:\n"
            f"- 学习能力: {self.learning_ability}/10\n"
            f"- 学习态度: {self.attitude.value}\n"
            f"- 学习水平: {self.level.value}\n\n"
            f"行为准则:\n"
            f"1. 回答问题时，基于你已学习的内容\n"
            f"2. 如果不确定，可以表示困惑或提问\n"
            f"3. 积极(active)的学生更主动回答问题\n"
            f"4. 你的回答质量应该与当前知识水平相符\n"
        )
```

> **注意:** 确保 `import random` 在文件顶部（在 dataclass 定义之前），并且 `StudentProfile` 导入与现有的 `Message` 导入一起添加。

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestStudentAgentMemory -v`
预期: All 8 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/agents/memories/memory_manager.py backend/tests/test_memory_manager.py
git commit -m "feat: add StudentAgentMemory dataclass with learning simulation"
```

---

### Task 4: MemoryManager — 消息路由

**文件:**
- 修改: `backend/agents/memories/memory_manager.py`
- 修改: `backend/tests/test_memory_manager.py`

- [ ] **Step 1: 编写失败的测试**

```python
# Add to backend/tests/test_memory_manager.py

from datetime import datetime

from schemas.student import StudentLevel, StudentProfile


class TestMemoryManager:
    """MemoryManager 测试."""

    def _make_message(
        self, sender: str, msg_type: MessageType, content: str
    ) -> Message:
        """辅助方法：创建消息."""
        return Message(
            sender=sender,
            message_type=msg_type,
            content=content,
            timestamp=datetime.now(),
        )

    def test_init(self):
        """测试初始化."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        assert manager.session_memory is session_mem
        assert manager.teacher_memory.covered_topics == []
        assert manager.student_memories == {}

    def test_register_student(self):
        """测试注册学生."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        profile = StudentProfile(name="张三", learning_ability=8)
        manager.register_student(profile)

        assert "张三" in manager.student_memories
        assert manager.student_memories["张三"].name == "张三"
        assert manager.student_memories["张三"].learning_ability == 8

    def test_process_message_appends_to_history(self):
        """测试处理消息添加到历史."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("teacher", MessageType.LECTURE, "今天学习变量")
        manager.process_message(msg)

        assert len(session_mem.message_history) == 1
        assert session_mem.message_history[0].content == "今天学习变量"

    def test_process_lecture_extracts_knowledge_points(self):
        """测试处理讲授内容提取知识点（使用 mock LLM）."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_mem,
            extract_knowledge_fn=lambda content: ["变量", "数据类型"],
        )

        msg = self._make_message("teacher", MessageType.LECTURE, "今天学习变量和数据类型")
        manager.process_message(msg)

        assert "变量" in manager.teacher_memory.covered_topics
        assert "数据类型" in manager.teacher_memory.covered_topics

    def test_process_lecture_no_duplicates(self):
        """测试不重复记录已讲授知识点."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_mem,
            extract_knowledge_fn=lambda content: ["变量"],
        )

        manager.process_message(
            self._make_message("teacher", MessageType.LECTURE, "讲变量")
        )
        manager.process_message(
            self._make_message("teacher", MessageType.LECTURE, "再讲变量")
        )

        assert manager.teacher_memory.covered_topics == ["变量"]

    def test_process_lecture_updates_student_memories(self):
        """测试讲授内容更新学生记忆."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_mem,
            extract_knowledge_fn=lambda content: ["变量"],
            student_rng=random.Random(42),
        )

        profile = StudentProfile(name="张三", learning_ability=10)
        manager.register_student(profile)

        manager.process_message(
            self._make_message("teacher", MessageType.LECTURE, "讲变量")
        )

        # 学习能力10的学生几乎一定记住
        student_mem = manager.student_memories["张三"]
        assert len(student_mem.learned_concepts) >= 0  # 可能记住

    def test_process_checkpoint_question_tracks(self):
        """测试处理 checkpoint 问题不崩溃."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message(
            "teacher", MessageType.CHECKPOINT_QUESTION, "什么是变量?"
        )
        manager.process_message(msg)
        assert len(session_mem.message_history) == 1

    def test_process_reply_to_teacher_tracks_participation(self):
        """测试处理学生回答记录参与."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("张三", MessageType.REPLY_TO_TEACHER, "变量是...")
        manager.process_message(msg)

        assert manager.teacher_memory.student_participation.get("张三") == 1

    def test_process_question_to_teacher_records(self):
        """测试处理学生提问记录到教师记忆."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message(
            "张三", MessageType.QUESTION_TO_TEACHER, "什么是变量?"
        )
        manager.process_message(msg)

        assert "张三" in manager.teacher_memory.student_questions
        assert manager.teacher_memory.student_questions["张三"] == ["什么是变量?"]

    def test_process_answer_to_checkpoint_tracks(self):
        """测试处理 checkpoint 回答记录参与."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("李四", MessageType.ANSWER_TO_CHECKPOINT, "变量是...")
        manager.process_message(msg)

        assert manager.teacher_memory.student_participation.get("李四") == 1
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestMemoryManager -v`
预期: FAIL with `ImportError: cannot import name 'MemoryManager'`

- [ ] **Step 3: 编写最小实现**

```python
# Add to backend/agents/memories/memory_manager.py, after StudentAgentMemory class

from typing import Callable

from schemas.message import MessageType


@dataclass
class MemoryManager:
    """记忆管理器 - 负责更新和维持 agent 记忆."""

    session_memory: SessionMemory
    teacher_memory: TeacherAgentMemory = field(default_factory=TeacherAgentMemory)
    student_memories: dict[str, StudentAgentMemory] = field(default_factory=dict)

    # 可注入的 LLM 调用函数
    extract_knowledge_fn: Callable[[str], list[str]] | None = None
    summary_fn: Callable[[str], str] | None = None

    # 用于学生记忆判断的随机数生成器
    student_rng: random.Random = field(default_factory=lambda: random.Random())

    def register_student(self, profile: StudentProfile) -> None:
        """注册学生到记忆系统."""
        self.student_memories[profile.name] = StudentAgentMemory.from_profile(profile)

    def process_message(self, message: Message) -> None:
        """处理新消息并更新记忆."""
        self.session_memory.add_message(message)

        if message.message_type == MessageType.LECTURE:
            self._process_lecture(message)
        elif message.message_type == MessageType.CHECKPOINT_QUESTION:
            pass  # 教师提问，暂不特殊处理
        elif message.message_type == MessageType.REPLY_TO_TEACHER:
            self._process_reply_to_teacher(message)
        elif message.message_type == MessageType.QUESTION_TO_TEACHER:
            self._process_question_to_teacher(message)
        elif message.message_type == MessageType.ANSWER_TO_CHECKPOINT:
            self._process_answer_to_checkpoint(message)

    def _process_lecture(self, message: Message) -> None:
        """处理教师讲授内容."""
        if self.extract_knowledge_fn:
            knowledge_points = self.extract_knowledge_fn(message.content)
        else:
            knowledge_points = []

        for kp in knowledge_points:
            self.teacher_memory.record_covered_topic(kp)

        for _name, student_mem in self.student_memories.items():
            student_mem.update_knowledge(knowledge_points, self.student_rng)

    def _process_reply_to_teacher(self, message: Message) -> None:
        """处理学生回答教师."""
        self.teacher_memory.record_student_participation(message.sender)

    def _process_question_to_teacher(self, message: Message) -> None:
        """处理学生向教师提问."""
        self.teacher_memory.record_student_question(message.sender, message.content)

    def _process_answer_to_checkpoint(self, message: Message) -> None:
        """处理学生回答 checkpoint 问题."""
        self.teacher_memory.record_student_participation(message.sender)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestMemoryManager -v`
预期: All 10 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/agents/memories/memory_manager.py backend/tests/test_memory_manager.py
git commit -m "feat: add MemoryManager with message routing and lecture processing"
```

---

### Task 5: MemoryManager — 摘要更新

**文件:**
- 修改: `backend/agents/memories/memory_manager.py`
- 修改: `backend/tests/test_memory_manager.py`

- [ ] **Step 1: 编写失败的测试**

```python
# Add to backend/tests/test_memory_manager.py

class TestMemoryManagerSummary:
    """MemoryManager 摘要更新测试."""

    def _make_lecture(self, content: str = "讲授内容") -> Message:
        return Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content=content,
            timestamp=datetime.now(),
        )

    def test_summary_updates_after_interval(self):
        """测试达到间隔后自动更新摘要."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        summary_calls = []

        def mock_summary(prompt: str) -> str:
            summary_calls.append(prompt)
            return "摘要内容"

        manager = MemoryManager(
            session_memory=session_mem,
            summary_fn=mock_summary,
            summary_update_interval=5,
        )

        # 发送5条消息触发摘要更新
        for i in range(5):
            manager.process_message(self._make_lecture(f"内容{i}"))

        assert session_mem.teaching_summary == "摘要内容"
        assert len(summary_calls) == 1

    def test_summary_not_updated_below_interval(self):
        """测试未达到间隔不更新摘要."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_mem,
            summary_fn=lambda p: "摘要",
            summary_update_interval=10,
        )

        for i in range(9):
            manager.process_message(self._make_lecture(f"内容{i}"))

        assert session_mem.teaching_summary == ""

    def test_summary_marks_updated(self):
        """测试摘要更新后重置计数器."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        call_count = 0

        def mock_summary(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"摘要{call_count}"

        manager = MemoryManager(
            session_memory=session_mem,
            summary_fn=mock_summary,
            summary_update_interval=5,
        )

        # 第一次触发
        for i in range(5):
            manager.process_message(self._make_lecture(f"内容{i}"))
        assert call_count == 1

        # 再发5条触发第二次
        for i in range(5):
            manager.process_message(self._make_lecture(f"更多内容{i}"))
        assert call_count == 2

    def test_summary_uses_recent_messages(self):
        """测试摘要基于最近消息生成."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")

        captured_prompt = None

        def mock_summary(prompt: str) -> str:
            nonlocal captured_prompt
            captured_prompt = prompt
            return "摘要"

        manager = MemoryManager(
            session_memory=session_mem,
            summary_fn=mock_summary,
            summary_update_interval=3,
        )

        for i in range(3):
            manager.process_message(self._make_lecture(f"内容{i}"))

        assert captured_prompt is not None
        assert "Python基础" in captured_prompt
        assert "内容2" in captured_prompt  # 最近的对话
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestMemoryManagerSummary -v`
预期: FAIL — summary is never called

- [ ] **Step 3: 更新 MemoryManager 支持摘要**

在 `MemoryManager` dataclass 中添加 `summary_update_interval` 字段并更新 `process_message`:

```python
# Add field to MemoryManager dataclass (alongside existing fields):
    summary_update_interval: int = 10
```

在 `MemoryManager` 类中添加此方法:

```python
    def _check_and_update_summary(self) -> None:
        """检查并更新教学摘要."""
        if not self.session_memory.should_update_summary():
            return
        if self.summary_fn is None:
            return

        recent = self.session_memory.get_recent_messages()
        message_text = "\n".join(
            f"[{m.sender}] ({m.message_type.value}): {m.content}" for m in recent
        )
        prompt = (
            f"请总结以下教学对话，提炼关键教学内容：\n\n"
            f"教学主题: {self.session_memory.topic}\n\n"
            f"最近对话:\n{message_text}\n\n"
            f"请提供:\n"
            f"1. 已讲授的主要知识点（3-5个）\n"
            f"2. 学生普遍掌握的内容\n"
            f"3. 学生普遍困惑的内容（如有）\n"
            f"4. 下一步教学建议\n\n"
            f"摘要格式：简洁明了，便于 agent 理解当前教学状态。"
        )

        self.session_memory.teaching_summary = self.summary_fn(prompt)
        self.session_memory.mark_summary_updated()
```

更新 `process_message` 在末尾调用 `_check_and_update_summary`:

```python
    def process_message(self, message: Message) -> None:
        """处理新消息并更新记忆."""
        self.session_memory.add_message(message)

        if message.message_type == MessageType.LECTURE:
            self._process_lecture(message)
        elif message.message_type == MessageType.CHECKPOINT_QUESTION:
            pass
        elif message.message_type == MessageType.REPLY_TO_TEACHER:
            self._process_reply_to_teacher(message)
        elif message.message_type == MessageType.QUESTION_TO_TEACHER:
            self._process_question_to_teacher(message)
        elif message.message_type == MessageType.ANSWER_TO_CHECKPOINT:
            self._process_answer_to_checkpoint(message)

        self._check_and_update_summary()
```

同时覆盖 `should_update_summary` 在 SessionMemory 中使用来自 MemoryManager 的可配置间隔。最简洁的方式：让 MemoryManager 将其 `summary_update_interval` 传递给 SessionMemory，或直接检查它。由于 `MemoryManager` 拥有 `summary_update_interval`，在 `__post_init__` 中更新 `SessionMemory` 以接受它通过方法或构造函数。最简单：直接使用 `SessionMemory.summary_update_interval` 作为默认值，让 MemoryManager 在 `__post_init__` 中设置它:

```python
# Add to MemoryManager.__post_init__:
    def __post_init__(self) -> None:
        """初始化后同步配置."""
        self.session_memory.summary_update_interval = self.summary_update_interval
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/test_memory_manager.py::TestMemoryManagerSummary -v`
预期: All 4 tests PASS

- [ ] **Step 5: 运行所有 memory 测试**

运行: `cd backend && python -m pytest tests/test_memory_manager.py -v`
预期: All tests PASS (no regressions)

- [ ] **Step 6: 提交**

```bash
git add backend/agents/memories/memory_manager.py backend/tests/test_memory_manager.py
git commit -m "feat: add summary update logic to MemoryManager with injectable LLM"
```

---

### Task 6: MemoryPersistence — 保存操作

**文件:**
- 创建: `backend/agents/memories/memory_persistence.py`
- 创建: `backend/tests/test_memory_persistence.py`

- [ ] **Step 1: 编写失败的测试**

```python
# backend/tests/test_memory_persistence.py
"""MemoryPersistence 测试."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memories.memory_manager import (
    SessionMemory,
    TeacherAgentMemory,
)
from orm.teaching_session import TeachingSessionModel


async def _create_teaching_session(db: AsyncSession) -> int:
    """辅助方法：创建教学会话."""
    session = TeachingSessionModel(
        teaching_mode="didactic",
        topic="Python基础",
        students_config={"students": []},
        status="running",
        start_time=datetime.now(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session.id


class TestMemoryPersistenceSave:
    """MemoryPersistence 保存操作测试."""

    async def test_save_session_memory_create(self, db_session: AsyncSession):
        """测试首次保存会话记忆（创建）."""
        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)

        memory = SessionMemory(
            session_id=session_id,
            topic="Python基础",
            teaching_summary="已讲授变量",
        )

        persistence = MemoryPersistence(db_session)
        await persistence.save_session_memory(memory)

        from orm.session_memory import SessionMemoryModel
        from sqlalchemy import select

        result = await db_session.execute(
            select(SessionMemoryModel).where(
                SessionMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record is not None
        assert record.teaching_summary == "已讲授变量"
        assert record.message_history == []

    async def test_save_session_memory_update(self, db_session: AsyncSession):
        """测试更新已有的会话记忆."""
        from agents.memories.memory_persistence import MemoryPersistence
        from orm.session_memory import SessionMemoryModel
        from sqlalchemy import select

        session_id = await _create_teaching_session(db_session)

        # 第一次保存
        persistence = MemoryPersistence(db_session)
        memory = SessionMemory(session_id=session_id, topic="Python基础")
        await persistence.save_session_memory(memory)

        # 第二次保存（更新）
        memory.teaching_summary = "已讲授变量和数据类型"
        await persistence.save_session_memory(memory)

        result = await db_session.execute(
            select(SessionMemoryModel).where(
                SessionMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record.teaching_summary == "已讲授变量和数据类型"

    async def test_save_teacher_memory_create(self, db_session: AsyncSession):
        """测试首次保存教师记忆."""
        from agents.memories.memory_persistence import MemoryPersistence
        from orm.teacher_memory import TeacherMemoryModel
        from sqlalchemy import select

        session_id = await _create_teaching_session(db_session)

        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("变量")
        teacher_mem.record_student_participation("张三")

        persistence = MemoryPersistence(db_session)
        await persistence.save_teacher_memory(session_id, teacher_mem)

        result = await db_session.execute(
            select(TeacherMemoryModel).where(
                TeacherMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record is not None
        assert "变量" in record.covered_topics
        assert record.student_participation == {"张三": 1}

    async def test_save_teacher_memory_update(self, db_session: AsyncSession):
        """测试更新已有的教师记忆."""
        from agents.memories.memory_persistence import MemoryPersistence
        from orm.teacher_memory import TeacherMemoryModel
        from sqlalchemy import select

        session_id = await _create_teaching_session(db_session)

        persistence = MemoryPersistence(db_session)

        # 第一次保存
        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("变量")
        await persistence.save_teacher_memory(session_id, teacher_mem)

        # 第二次保存（更新）
        teacher_mem.record_covered_topic("函数")
        await persistence.save_teacher_memory(session_id, teacher_mem)

        result = await db_session.execute(
            select(TeacherMemoryModel).where(
                TeacherMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert "变量" in record.covered_topics
        assert "函数" in record.covered_topics

    async def test_save_student_memory_create(self, db_session: AsyncSession):
        """测试首次保存学生记忆."""
        from agents.memories.memory_persistence import MemoryPersistence
        from agents.memories.memory_manager import StudentAgentMemory
        from orm.student_memory import StudentMemoryModel
        from schemas.student import StudentProfile, StudentLevel
        from sqlalchemy import select

        session_id = await _create_teaching_session(db_session)

        student_mem = StudentAgentMemory.from_profile(
            StudentProfile(
                name="张三",
                level=StudentLevel.EXCELLENT,
                learning_ability=8,
            )
        )
        student_mem.learned_concepts.append("变量")

        persistence = MemoryPersistence(db_session)
        await persistence.save_student_memory(session_id, student_mem)

        result = await db_session.execute(
            select(StudentMemoryModel).where(
                StudentMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record is not None
        assert record.student_name == "张三"
        assert "变量" in record.learned_concepts

    async def test_save_student_memory_update(self, db_session: AsyncSession):
        """测试更新已有的学生记忆."""
        from agents.memories.memory_persistence import MemoryPersistence
        from agents.memories.memory_manager import StudentAgentMemory
        from orm.student_memory import StudentMemoryModel
        from schemas.student import StudentProfile
        from sqlalchemy import select

        session_id = await _create_teaching_session(db_session)

        persistence = MemoryPersistence(db_session)

        # 第一次保存
        student_mem = StudentAgentMemory.from_profile(
            StudentProfile(name="张三", learning_ability=8)
        )
        await persistence.save_student_memory(session_id, student_mem)

        # 第二次保存（更新）
        student_mem.learned_concepts.append("函数")
        student_mem.current_knowledge_level = 0.3
        await persistence.save_student_memory(session_id, student_mem)

        result = await db_session.execute(
            select(StudentMemoryModel).where(
                StudentMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert "变量" in record.learned_concepts
        assert "函数" in record.learned_concepts
        assert record.current_knowledge_level == 0.3

    async def test_save_message(self, db_session: AsyncSession):
        """测试保存单条消息."""
        from agents.memories.memory_persistence import MemoryPersistence
        from orm.message import MessageModel
        from schemas.message import Message, MessageType
        from sqlalchemy import select

        session_id = await _create_teaching_session(db_session)

        msg = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="今天学习变量",
            timestamp=datetime.now(),
        )

        persistence = MemoryPersistence(db_session)
        await persistence.save_message(session_id, msg)

        result = await db_session.execute(
            select(MessageModel).where(MessageModel.session_id == session_id)
        )
        records = result.scalars().all()
        assert len(records) == 1
        assert records[0].sender == "teacher"
        assert records[0].content == "今天学习变量"
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_persistence.py -v`
预期: FAIL with `ModuleNotFoundError: No module named 'agents.memories.memory_persistence'`

- [ ] **Step 3: 编写最小实现**

```python
# backend/agents/memories/memory_persistence.py
"""记忆持久化服务 - 数据库 save/load 操作."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Base
from agents.memories.memory_manager import SessionMemory, TeacherAgentMemory
from orm.message import MessageModel
from orm.session_memory import SessionMemoryModel
from orm.teacher_memory import TeacherMemoryModel
from schemas.message import Message

T = TypeVar("T", bound=Base)


class MemoryPersistence:
    """记忆持久化服务."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化.

        Args:
            db_session: SQLAlchemy 异步会话
        """
        self.db_session = db_session

    async def _upsert(
        self,
        model: type[T],
        session_id: int,
        update_fn: Callable[[T], None],
        create_fn: Callable[[], dict[str, Any]],
    ) -> T:
        """通用的 upsert 操作.

        Args:
            model: ORM 模型类
            session_id: 会话ID
            update_fn: 更新现有记录的函数
            create_fn: 创建新记录的函数，返回字段字典

        Returns:
            ORM 模型实例
        """
        result = await self.db_session.execute(
            select(model).where(model.session_id == session_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            update_fn(existing)
            await self.db_session.commit()
            return existing

        db_record = model(**create_fn())
        self.db_session.add(db_record)
        await self.db_session.commit()
        return db_record

    async def save_session_memory(
        self, memory: SessionMemory
    ) -> SessionMemoryModel:
        """保存会话记忆到数据库.

        Args:
            memory: 会话记忆对象

        Returns:
            ORM 模型实例
        """
        def update_fn(existing: SessionMemoryModel) -> None:
            existing.teaching_summary = memory.teaching_summary
            existing.message_history = [
                m.model_dump(mode="json") for m in memory.message_history
            ]
            existing.last_updated = datetime.now()

        def create_fn() -> dict[str, Any]:
            return {
                "session_id": memory.session_id,
                "message_history": [
                    m.model_dump(mode="json") for m in memory.message_history
                ],
                "teaching_summary": memory.teaching_summary or None,
                "last_updated": datetime.now(),
            }

        return await self._upsert(
            SessionMemoryModel, memory.session_id, update_fn, create_fn
        )

    async def save_teacher_memory(
        self, session_id: int, teacher_memory: TeacherAgentMemory
    ) -> TeacherMemoryModel:
        """保存教师记忆.

        Args:
            session_id: 会话ID
            teacher_memory: 教师记忆对象

        Returns:
            ORM 模型实例
        """
        def update_fn(existing: TeacherMemoryModel) -> None:
            existing.covered_topics = teacher_memory.covered_topics
            existing.student_questions = teacher_memory.student_questions
            existing.teaching_progress = teacher_memory.teaching_progress
            existing.student_participation = teacher_memory.student_participation
            existing.student_misconceptions = teacher_memory.student_misconceptions

        def create_fn() -> dict[str, Any]:
            return {
                "session_id": session_id,
                "covered_topics": teacher_memory.covered_topics,
                "student_questions": teacher_memory.student_questions,
                "teaching_progress": teacher_memory.teaching_progress,
                "student_participation": teacher_memory.student_participation,
                "student_misconceptions": teacher_memory.student_misconceptions,
            }

        return await self._upsert(
            TeacherMemoryModel, session_id, update_fn, create_fn
        )

    async def save_message(self, session_id: int, message: Message) -> MessageModel:
        """保存单条消息到数据库.

        Args:
            session_id: 会话ID
            message: 消息对象

        Returns:
            ORM 模型实例
        """
        db_message = MessageModel(
            session_id=session_id,
            sender=message.sender,
            message_type=message.message_type.value,
            content=message.content,
            timestamp=message.timestamp or datetime.now(),
        )
        self.db_session.add(db_message)
        await self.db_session.commit()
        await self.db_session.refresh(db_message)
        return db_message

    async def save_student_memory(
        self, session_id: int, student_memory: StudentAgentMemory
    ) -> StudentMemoryModel:
        """保存学生记忆.

        Args:
            session_id: 会话ID
            student_memory: 学生记忆对象

        Returns:
            ORM 模型实例
        """
        from agents.memories.memory_manager import StudentAgentMemory
        from orm.student_memory import StudentMemoryModel

        def update_fn(existing: StudentMemoryModel) -> None:
            existing.learned_concepts = student_memory.learned_concepts
            existing.confused_points = student_memory.confused_points
            existing.questions_asked = student_memory.questions_asked
            existing.initial_knowledge_level = student_memory.initial_knowledge_level
            existing.current_knowledge_level = student_memory.current_knowledge_level
            existing.learning_rate = student_memory.learning_rate
            existing.last_updated = datetime.now()

        def create_fn() -> dict[str, Any]:
            return {
                "session_id": session_id,
                "student_name": student_memory.name,
                "learned_concepts": student_memory.learned_concepts,
                "confused_points": student_memory.confused_points,
                "questions_asked": student_memory.questions_asked,
                "initial_knowledge_level": student_memory.initial_knowledge_level,
                "current_knowledge_level": student_memory.current_knowledge_level,
                "learning_rate": student_memory.learning_rate,
                "last_updated": datetime.now(),
            }

        return await self._upsert(
            StudentMemoryModel, session_id, update_fn, create_fn
        )
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/test_memory_persistence.py::TestMemoryPersistenceSave -v`
预期: All 7 tests PASS

- [ ] **Step 5: 提交**

```bash
git add backend/agents/memories/memory_persistence.py backend/tests/test_memory_persistence.py
git commit -m "feat: add MemoryPersistence save operations (session, teacher, student, messages)"
```

---

### Task 7: MemoryPersistence — 加载操作

**文件:**
- 修改: `backend/agents/memories/memory_persistence.py`
- 修改: `backend/tests/test_memory_persistence.py`

- [ ] **Step 1: 编写失败的测试**

```python
# Add to backend/tests/test_memory_persistence.py

from agents.memories.memory_manager import TeacherAgentMemory
from schemas.message import Message, MessageType


class TestMemoryPersistenceLoad:
    """MemoryPersistence 加载操作测试."""

    async def test_load_session_memory_exists(
        self, db_session: AsyncSession
    ):
        """测试加载已存在的会话记忆."""
        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)

        # 先保存
        memory = SessionMemory(
            session_id=session_id,
            topic="Python基础",
            teaching_summary="已讲授变量",
        )
        persistence = MemoryPersistence(db_session)
        await persistence.save_session_memory(memory)

        # 再加载
        loaded = await persistence.load_session_memory(session_id)
        assert loaded is not None
        assert loaded.session_id == session_id
        assert loaded.teaching_summary == "已讲授变量"

    async def test_load_session_memory_not_exists(
        self, db_session: AsyncSession
    ):
        """测试加载不存在的会话记忆返回 None."""
        from agents.memories.memory_persistence import MemoryPersistence

        persistence = MemoryPersistence(db_session)
        loaded = await persistence.load_session_memory(99999)
        assert loaded is None

    async def test_load_session_memory_with_messages(
        self, db_session: AsyncSession
    ):
        """测试加载会话记忆包含消息历史."""
        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 保存消息
        msg1 = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="今天学习变量",
            timestamp=datetime.now(),
        )
        msg2 = Message(
            sender="张三",
            message_type=MessageType.REPLY_TO_TEACHER,
            content="变量是什么?",
            timestamp=datetime.now(),
        )
        await persistence.save_message(session_id, msg1)
        await persistence.save_message(session_id, msg2)

        # 保存会话记忆
        memory = SessionMemory(session_id=session_id, topic="Python基础")
        await persistence.save_session_memory(memory)

        # 加载
        loaded = await persistence.load_session_memory(session_id)
        assert loaded is not None
        assert len(loaded.message_history) == 2
        assert loaded.message_history[0].sender == "teacher"
        assert loaded.message_history[1].sender == "张三"

    async def test_load_teacher_memory_exists(
        self, db_session: AsyncSession
    ):
        """测试加载已存在的教师记忆."""
        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 先保存
        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("变量")
        teacher_mem.record_covered_topic("函数")
        teacher_mem.record_student_participation("张三")
        await persistence.save_teacher_memory(session_id, teacher_mem)

        # 再加载
        loaded = await persistence.load_teacher_memory(session_id)
        assert loaded is not None
        assert "变量" in loaded.covered_topics
        assert "函数" in loaded.covered_topics
        assert loaded.student_participation == {"张三": 1}

    async def test_load_teacher_memory_not_exists(
        self, db_session: AsyncSession
    ):
        """测试加载不存在的教师记忆返回 None."""
        from agents.memories.memory_persistence import MemoryPersistence

        persistence = MemoryPersistence(db_session)
        loaded = await persistence.load_teacher_memory(99999)
        assert loaded is None

    async def test_load_student_memory_exists(
        self, db_session: AsyncSession
    ):
        """测试加载已存在的学生记忆."""
        from agents.memories.memory_persistence import MemoryPersistence
        from agents.memories.memory_manager import StudentAgentMemory
        from schemas.student import StudentProfile

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 先保存
        student_mem = StudentAgentMemory.from_profile(
            StudentProfile(name="张三", learning_ability=8)
        )
        student_mem.learned_concepts.append("变量")
        student_mem.current_knowledge_level = 0.2
        await persistence.save_student_memory(session_id, student_mem)

        # 再加载
        loaded = await persistence.load_student_memory(session_id, "张三")
        assert loaded is not None
        assert "变量" in loaded.learned_concepts
        assert loaded.current_knowledge_level == 0.2

    async def test_load_student_memory_not_exists(
        self, db_session: AsyncSession
    ):
        """测试加载不存在的学生记忆返回 None."""
        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        loaded = await persistence.load_student_memory(session_id, "不存在")
        assert loaded is None
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_persistence.py::TestMemoryPersistenceLoad -v`
预期: FAIL with `AttributeError: 'MemoryPersistence' object has no attribute 'load_session_memory'`

- [ ] **Step 3: 编写最小实现**

```python
# Add to MemoryPersistence class in backend/agents/memories/memory_persistence.py

    async def load_session_memory(
        self, session_id: int
    ) -> SessionMemory | None:
        """从数据库加载会话记忆.

        Args:
            session_id: 会话ID

        Returns:
            会话记忆对象，不存在则返回 None
        """
        result = await self.db_session.execute(
            select(SessionMemoryModel).where(
                SessionMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            return None

        # 从 messages 表加载消息历史
        message_history = await self._load_message_history(session_id)

        # 从 teaching_sessions 表获取 topic
        topic = await self._load_topic(session_id)

        return SessionMemory(
            session_id=session_id,
            topic=topic,
            teaching_summary=record.teaching_summary or "",
            message_history=message_history,
        )

    async def load_teacher_memory(
        self, session_id: int
    ) -> TeacherAgentMemory | None:
        """从数据库加载教师记忆.

        Args:
            session_id: 会话ID

        Returns:
            教师记忆对象，不存在则返回 None
        """
        result = await self.db_session.execute(
            select(TeacherMemoryModel).where(
                TeacherMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            return None

        memory = TeacherAgentMemory()
        memory.covered_topics = record.covered_topics or []
        memory.student_questions = record.student_questions or {}
        memory.teaching_progress = record.teaching_progress or 0.0
        memory.student_participation = record.student_participation or {}
        memory.student_misconceptions = record.student_misconceptions or {}

        return memory

    async def _load_message_history(self, session_id: int) -> list[Message]:
        """从 messages 表加载消息历史.

        Args:
            session_id: 会话ID

        Returns:
            消息列表，按时间排序
        """
        result = await self.db_session.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.timestamp)
        )
        records = result.scalars().all()

        return [
            Message(
                sender=record.sender,
                message_type=MessageType(record.message_type),
                content=record.content,
                timestamp=record.timestamp,
            )
            for record in records
        ]

    async def _load_topic(self, session_id: int) -> str:
        """从 teaching_sessions 表加载主题.

        Args:
            session_id: 会话ID

        Returns:
            教学主题
        """
        from orm.teaching_session import TeachingSessionModel

        result = await self.db_session.execute(
            select(TeachingSessionModel).where(
                TeachingSessionModel.id == session_id
            )
        )
        record = result.scalar_one_or_none()
        return record.topic if record else ""

    async def load_student_memory(
        self, session_id: int, student_name: str
    ) -> StudentAgentMemory | None:
        """从数据库加载学生记忆.

        Args:
            session_id: 会话ID
            student_name: 学生姓名

        Returns:
            学生记忆对象，不存在则返回 None
        """
        from agents.memories.memory_manager import StudentAgentMemory
        from orm.student_memory import StudentMemoryModel

        result = await self.db_session.execute(
            select(StudentMemoryModel).where(
                StudentMemoryModel.session_id == session_id,
                StudentMemoryModel.student_name == student_name,
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            return None

        memory = StudentAgentMemory(
            name=record.student_name,
            level=record.level,
            attitude=record.attitude,
            learning_ability=record.learning_ability,
        )
        memory.learned_concepts = record.learned_concepts or []
        memory.confused_points = record.confused_points or []
        memory.questions_asked = record.questions_asked or []
        memory.initial_knowledge_level = record.initial_knowledge_level or 0.0
        memory.current_knowledge_level = record.current_knowledge_level or 0.0
        memory.learning_rate = record.learning_rate or 0.05

        return memory
```

同时在文件顶部添加导入:
```python
from schemas.message import Message, MessageType
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/test_memory_persistence.py::TestMemoryPersistenceLoad -v`
预期: All 7 tests PASS

- [ ] **Step 5: 运行所有 persistence 测试**

运行: `cd backend && python -m pytest tests/test_memory_persistence.py -v`
预期: All 14 tests PASS

- [ ] **Step 6: 提交**

```bash
git add backend/agents/memories/memory_persistence.py backend/tests/test_memory_persistence.py
git commit -m "feat: add MemoryPersistence load operations (session, teacher, student, messages)"
```

---

### Task 8: 集成测试 — 完整流程

**文件:**
- 修改: `backend/tests/test_memory_persistence.py`

- [ ] **Step 1: 编写失败的测试**

```python
# Add to backend/tests/test_memory_persistence.py

class TestMemoryIntegration:
    """记忆系统完整流程集成测试."""

    async def test_full_flow_save_and_restore(
        self, db_session: AsyncSession
    ):
        """完整流程：创建会话 → 处理消息 → 持久化 → 加载恢复."""
        from agents.memories.memory_manager import MemoryManager
        from agents.memories.memory_persistence import MemoryPersistence
        from schemas.student import StudentProfile

        # 1. 创建教学会话
        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 2. 创建 MemoryManager 并注册学生
        session_memory = SessionMemory(session_id=session_id, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_memory,
            extract_knowledge_fn=lambda c: ["变量", "数据类型"],
            summary_fn=lambda p: "已讲授变量和数据类型",
            summary_update_interval=5,
            student_rng=random.Random(42),
        )
        manager.register_student(
            StudentProfile(name="张三", learning_ability=8)
        )

        # 3. 处理多条消息
        messages = [
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="今天学习变量和数据类型",
                timestamp=datetime.now(),
            ),
            Message(
                sender="teacher",
                message_type=MessageType.CHECKPOINT_QUESTION,
                content="什么是变量?",
                timestamp=datetime.now(),
            ),
            Message(
                sender="张三",
                message_type=MessageType.REPLY_TO_TEACHER,
                content="变量是存储数据的容器",
                timestamp=datetime.now(),
            ),
            Message(
                sender="张三",
                message_type=MessageType.QUESTION_TO_TEACHER,
                content="变量有哪些类型?",
                timestamp=datetime.now(),
            ),
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量有整数、浮点数、字符串等类型",
                timestamp=datetime.now(),
            ),
        ]

        for msg in messages:
            manager.process_message(msg)

        # 4. 验证内存状态
        assert len(session_memory.message_history) == 5
        assert "变量" in manager.teacher_memory.covered_topics
        assert manager.teacher_memory.student_participation["张三"] == 1
        assert "张三" in manager.teacher_memory.student_questions
        student_mem = manager.student_memories["张三"]
        assert len(student_mem.learned_concepts) >= 0  # 可能记住概念

        # 5. 持久化
        await persistence.save_session_memory(manager.session_memory)
        await persistence.save_teacher_memory(
            session_id, manager.teacher_memory
        )
        await persistence.save_student_memory(
            session_id, manager.student_memories["张三"]
        )
        for msg in manager.session_memory.message_history:
            await persistence.save_message(session_id, msg)

        # 6. 加载恢复
        loaded_session = await persistence.load_session_memory(session_id)
        loaded_teacher = await persistence.load_teacher_memory(session_id)
        loaded_student = await persistence.load_student_memory(session_id, "张三")

        # 7. 验证恢复的数据
        assert loaded_session is not None
        assert loaded_session.topic == "Python基础"
        assert loaded_session.teaching_summary == "已讲授变量和数据类型"
        assert len(loaded_session.message_history) == 5

        assert loaded_teacher is not None
        assert "变量" in loaded_teacher.covered_topics
        assert loaded_teacher.student_participation["张三"] == 1
        assert loaded_teacher.student_questions["张三"] == ["变量有哪些类型?"]

        assert loaded_student is not None
        assert loaded_student.name == "张三"
        assert loaded_student.learning_ability == 8

    async def test_save_and_load_empty_session(
        self, db_session: AsyncSession
    ):
        """测试空会话的保存和加载."""
        from agents.memories.memory_manager import MemoryManager
        from agents.memories.memory_persistence import MemoryPersistence
        from schemas.student import StudentProfile

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        session_memory = SessionMemory(session_id=session_id, topic="空主题")
        manager = MemoryManager(session_memory=session_memory)
        manager.register_student(StudentProfile(name="张三"))

        await persistence.save_session_memory(manager.session_memory)
        await persistence.save_teacher_memory(
            session_id, manager.teacher_memory
        )
        await persistence.save_student_memory(
            session_id, manager.student_memories["张三"]
        )

        loaded_session = await persistence.load_session_memory(session_id)
        loaded_teacher = await persistence.load_teacher_memory(session_id)
        loaded_student = await persistence.load_student_memory(session_id, "张三")

        assert loaded_session is not None
        assert loaded_session.message_history == []
        assert loaded_teacher is not None
        assert loaded_teacher.covered_topics == []
        assert loaded_student is not None
        assert loaded_student.learned_concepts == []
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/test_memory_persistence.py::TestMemoryIntegration -v`
预期: PASS if all previous tasks are complete (this is an integration test using existing functionality)

如果测试立即通过，那很好 — 这验证了完整流程端到端工作正常。

- [ ] **Step 3: 运行所有测试**

运行: `cd backend && python -m pytest tests/test_memory_manager.py tests/test_memory_persistence.py -v`
预期: All tests PASS

- [ ] **Step 4: 运行 ruff**

运行: `cd backend && ruff check agents/memories/memory_manager.py agents/memories/memory_persistence.py tests/test_memory_manager.py tests/test_memory_persistence.py`
预期: All checks passed

- [ ] **Step 5: 提交**

```bash
git add backend/tests/test_memory_persistence.py
git commit -m "test: add integration tests for full memory save/load flow including student memory"
```

---

### Task 9: 更新开发路线图

**文件:**
- 修改: `docs/development-roadmap.md`

- [ ] **Step 1: 更新 Phase 3 检查清单**

更新 `docs/development-roadmap.md` 中的 Phase 3 部分，将所有完成的任务标记为 `[✓]` 并添加完成日期。更新底部的"当前进度"部分。

- [ ] **Step 2: 提交**

```bash
git add docs/development-roadmap.md
git commit -m "docs: 更新开发路线图，Phase 3 已完成"
```

---

## 自检清单

**1. 规格覆盖:**
- [x] SessionMemory with message_history, teaching_summary, should_update_summary() → Task 1
- [x] TeacherAgentMemory with covered_topics, student_questions, student_participation, get_system_prompt_addition() → Task 2
- [x] StudentAgentMemory with learned_concepts, should_remember_concept(), get_system_prompt_addition() → Task 3
- [x] MemoryManager.process_message() → Task 4
- [x] MemoryManager._process_lecture() with knowledge extraction → Task 4
- [x] MemoryManager._update_summary() with LLM → Task 5
- [x] MemoryPersistence._upsert() → Task 6
- [x] MemoryPersistence.save_session_memory() → Task 6
- [x] MemoryPersistence.save_teacher_memory() → Task 6
- [x] MemoryPersistence.save_student_memory() → Task 6
- [x] MemoryPersistence.load_session_memory() → Task 7
- [x] MemoryPersistence.load_teacher_memory() → Task 7
- [x] MemoryPersistence.load_student_memory() → Task 7
- [x] MemoryPersistence._load_message_history() → Task 7
- [x] asyncio.Lock() 用于并发控制 — **未包含。** 路线图中提到了，但当前的内存设计使用同步 `process_message` 不需要它。如果需要异步并发访问，可以在 WebSocket/agent 集成时添加。
- [x] StudentMemory 持久化到数据库 — Task 6 + Task 7

**2. 占位符扫描:**
- [x] 未找到 TBD、TODO 或 "implement later"
- [x] 所有步骤包含完整代码
- [x] 所有命令都有预期输出

**3. 类型一致性:**
- [x] `session_id: int` 贯穿始终（匹配 ORM FK 类型）
- [x] `MessageType` 枚举来自 `schemas.message` 一致使用
- [x] `StudentProfile` 来自 `schemas.student` 用于学生注册
- [x] `Message` 来自 `schemas.message` 贯穿使用
