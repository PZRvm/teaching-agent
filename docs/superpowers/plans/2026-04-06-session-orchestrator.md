# Phase 7: SessionOrchestrator (观察模式核心) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现观察模式的自动教学流程编排，基于检查点系统驱动教学流程。

**Architecture:** SessionOrchestrator 作为观察模式的核心控制器，遍历检查点计划，协调 TeacherAgent 和 StudentAgent 交互，通过 WebSocket 推送状态更新，集成 MemoryManager 记录教学过程。

**Tech Stack:** Python 3.12+, AsyncIO, FastAPI, WebSocket, SQLAlchemy, Pydantic, LangChain

---

## 作业流程说明 (Homework Flow)

观察模式中，作业流程在所有检查点完成后执行。以下是完整的作业流程：

### 流程图

```
所有检查点完成 → 布置作业 → 收集作业 → 评分 → 结束反馈 → 学生反馈
         ↓           ↓          ↓        ↓         ↓         ↓
   assign_homework  submit  grade_homework  end_feedback  give_feedback
```

### 详细步骤

1. **布置作业** (`assign_homework`)
   - 调用时机：最后一个检查点状态变为 `COMPLETE` 后
   - 调用方法：`TeacherAgent.assign_homework()`
   - 消息类型：`MessageType.ASSIGN_HOMEWORK`
   - 接收者：`"all"`（所有学生）

2. **收集作业提交** (`submit_homework`)
   - 调用方法：`StudentAgent.submit_homework(homework_prompt)`
   - 学生基于其 `level`、`attitude`、`learning_ability` 参数生成作业结果
   - **注意**：学生不需要模拟"做作业"的思考和过程，直接返回作业结果
   - 消息类型：`MessageType.HOMEWORK_SUBMISSION`
   - 接收者：`"teacher"`

3. **教师评分** (`grade_homework`)
   - 调用方法：`TeacherAgent.grade_homework(student_name, homework_content)`
   - 教师为每个学生的作业提供反馈
   - 消息类型：`MessageType.HOMEWORK_FEEDBACK`
   - 接收者：具体学生名称

4. **教师结束反馈** (`end_feedback`)
   - 调用方法：`TeacherAgent.end_feedback()`
   - 教师对整个课程进行总结反馈
   - 消息类型：`MessageType.END_FEEDBACK`
   - 接收者：`"all"`

5. **学生课程反馈** (`give_feedback`)
   - 调用方法：`StudentAgent.give_feedback(prompt)`
   - 每个学生对课程提供反馈
   - 消息类型：`MessageType.FEEDBACK_SUBMISSION`
   - 接收者：`"teacher"`

### 实现位置

作业流程在 `SessionOrchestrator` 类中实现：
- `_assign_homework()` - 私有方法，布置作业
- `_collect_homework_and_feedback()` - 私有方法，收集作业和反馈

这些方法在 `run_autonomous_session()` 的末尾被调用：

```python
# 所有检查点完成后
await self._assign_homework()
await self._collect_homework_and_feedback()
```

### 与 design.md 对应

此流程对应 `docs/design.md` 第 1002-1003 行描述的作业架构。
注意：`design.md` 中提到的 `do_homework` 消息类型在当前实现中被简化，
学生直接调用 `submit_homework()` 生成结果，不需要单独的"做作业"消息类型。

---

## File Structure

**New files:**
- `backend/models/session/orchestrator.py` - SessionOrchestrator 类
- `backend/models/session/__init__.py` - 模块导出
- `backend/models/observation/router.py` - 观察模式 API 路由
- `backend/models/observation/schemas.py` - 观察模式 Pydantic schemas
- `backend/models/observation/__init__.py` - 模块导出
- `backend/models/session/router_websocket.py` - WebSocket 端点
- `backend/tests/units/test_session_orchestrator.py` - 单元测试
- `backend/tests/integration/test_observation_api.py` - 集成测试

**Modified files:**
- `backend/schemas/message.py` - 添加 receiver 字段

---

## Task 1: Message Schema 扩展

**Files:**
- Modify: `backend/schemas/message.py:25-31`
- Test: `backend/tests/units/test_schemas.py`

### 步骤 1: 写失败的测试

```python
def test_message_with_receiver():
    """测试 Message 支持 receiver 字段."""
    from datetime import datetime
    from schemas.message import Message, MessageType

    msg = Message(
        sender="teacher",
        message_type=MessageType.LECTURE,
        content="Hello",
        receiver="all",
        timestamp=datetime.now()
    )
    assert msg.receiver == "all"
```

### 步骤 2: 运行测试验证失败

```bash
cd backend
pytest tests/units/test_schemas.py::test_message_with_receiver -v
```

Expected: FAIL - "Message类型没有receiver字段"

### 步骤 3: 实现最小代码

修改 `backend/schemas/message.py` 的 Message 类：

```python
class Message(BaseModel):
    """消息数据模型"""

    sender: str = Field(description="发送者")
    message_type: MessageType = Field(description="消息类型")
    content: str = Field(min_length=1, description="消息内容")
    receiver: str = Field(default="all", description="接收者 (all/学生名称)")
    timestamp: datetime | None = Field(None)
```

同时更新 MessageCreate 和 MessageResponse：

```python
class MessageCreate(BaseModel):
    """创建消息请求"""

    session_id: int = Field(description="会话ID")
    sender: str = Field(description="发送者")
    message_type: MessageType = Field(description="消息类型")
    content: str = Field(min_length=1, description="消息内容")
    receiver: str = Field(default="all", description="接收者")
```

```python
class MessageResponse(BaseModel):
    """消息响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sender: str
    message_type: MessageType
    content: str
    receiver: str
    timestamp: datetime
```

### 步骤 4: 运行测试验证通过

```bash
pytest tests/units/test_schemas.py::test_message_with_receiver -v
```

Expected: PASS

### 步骤 5: 提交

```bash
git add backend/schemas/message.py backend/tests/units/test_schemas.py
git commit -m "feat: add receiver field to Message schema"
```

---

## Task 2: SessionOrchestrator 基础结构

**Files:**
- Create: `backend/models/session/orchestrator.py`
- Create: `backend/models/session/__init__.py`
- Test: `backend/tests/units/test_session_orchestrator.py`

### 步骤 1: 写失败的测试 - 初始化

```python
def test_orchestrator_init():
    """测试 SessionOrchestrator 初始化."""
    from agents.memories import SessionMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.teacher_agent import TeacherAgent
    from agents.student_agent import StudentAgent
    from models.checkpoint.schemas import CheckpointPlan, Checkpoint, CheckpointState
    from schemas.student import StudentProfile, StudentLevel, StudentAttitude
    from unittest.mock import Mock

    # 创建 mock LLM
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value="Test response")

    # 创建 session memory
    session_memory = SessionMemory(topic="Test Topic")
    memory_manager = MemoryManager(session_memory=session_memory)

    # 创建 teacher agent
    teacher = TeacherAgent(
        session_memory=session_memory,
        llm=mock_llm,
        teaching_mode="heuristic",
        memory_manager=memory_manager
    )

    # 创建学生 profile
    student_profile = StudentProfile(
        name="TestStudent",
        level=StudentLevel.AVERAGE,
        attitude=StudentAttitude.NEUTRAL
    )

    # 创建 student agent
    student = StudentAgent(
        session_memory=session_memory,
        llm=mock_llm,
        profile=student_profile
    )

    # 创建 checkpoint plan
    plan = CheckpointPlan(
        topic="Test Topic",
        teaching_mode="heuristic",
        checkpoints=[
            Checkpoint(
                title="CP1",
                key_point="Point 1",
                checkpoint_question="Question 1?"
            )
        ]
    )

    # 创建 orchestrator
    from models.session.orchestrator import SessionOrchestrator

    orchestrator = SessionOrchestrator(
        teacher_agent=teacher,
        student_agents=[student],
        checkpoint_plan=plan,
        memory_manager=memory_manager
    )

    assert orchestrator.teacher_agent == teacher
    assert orchestrator.student_agents == [student]
    assert orchestrator.checkpoint_plan == plan
    assert orchestrator.memory_manager == memory_manager
```

### 步骤 2: 运行测试验证失败

```bash
cd backend
pytest tests/units/test_session_orchestrator.py::test_orchestrator_init -v
```

Expected: FAIL - "No module named 'models.session.orchestrator'"

### 步骤 3: 实现最小代码

创建 `backend/models/session/__init__.py`:

```python
"""Session 模型包."""

from models.session.orchestrator import SessionOrchestrator

__all__ = ["SessionOrchestrator"]
```

创建 `backend/models/session/orchestrator.py`:

```python
"""SessionOrchestrator - 观察模式核心控制器."""

from agents.memories.memory_manager import MemoryManager
from agents.teacher_agent import TeacherAgent
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from agents.student_agent import StudentAgent


class SessionOrchestrator:
    """观察模式自动教学流程编排器.

    基于检查点系统驱动教学流程：
    - 遍历检查点数组
    - 协调教师和学生 agent 交互
    - 通过 WebSocket 推送状态更新
    - 集成 MemoryManager 记录教学过程
    """

    def __init__(
        self,
        *,
        teacher_agent: TeacherAgent,
        student_agents: list[StudentAgent],
        checkpoint_plan: CheckpointPlan,
        memory_manager: MemoryManager,
    ):
        """初始化编排器.

        Args:
            teacher_agent: 教师 agent
            student_agents: 学生 agent 列表
            checkpoint_plan: 检查点计划
            memory_manager: 记忆管理器
        """
        self.teacher_agent = teacher_agent
        self.student_agents = student_agents
        self.checkpoint_plan = checkpoint_plan
        self.memory_manager = memory_manager
```

### 步骤 4: 运行测试验证通过

```bash
pytest tests/units/test_session_orchestrator.py::test_orchestrator_init -v
```

Expected: PASS

### 步骤 5: 提交

```bash
git add backend/models/session/ backend/tests/units/test_session_orchestrator.py
git commit -m "feat: add SessionOrchestrator basic structure"
```

---

## Task 3: run_autonomous_session() 主循环

**Files:**
- Modify: `backend/models/session/orchestrator.py`
- Test: `backend/tests/units/test_session_orchestrator.py`

### 步骤 1: 写失败的测试

```python
def test_run_autonomous_session_basic():
    """测试 run_autonomous_session 基本流程."""
    import asyncio
    from agents.memories import SessionMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.teacher_agent import TeacherAgent
    from agents.student_agent import StudentAgent
    from models.checkpoint.schemas import CheckpointPlan, Checkpoint, CheckpointState
    from schemas.student import StudentProfile, StudentLevel, StudentAttitude
    from unittest.mock import Mock, AsyncMock, patch
    from models.session.orchestrator import SessionOrchestrator

    async def test():
        # Mock LLM
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value="Test content")

        session_memory = SessionMemory(topic="Test Topic")
        memory_manager = MemoryManager(session_memory=session_memory)

        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=memory_manager
        )

        student_profile = StudentProfile(
            name="Student1",
            level=StudentLevel.AVERAGE,
            attitude=StudentAttitude.NEUTRAL
        )

        student = StudentAgent(
            session_memory=session_memory,
            llm=mock_llm,
            profile=student_profile
        )

        # 创建包含 2 个检查点的计划
        plan = CheckpointPlan(
            topic="Test",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(title="CP1", key_point="Point 1", checkpoint_question="Q1?"),
                Checkpoint(title="CP2", key_point="Point 2", checkpoint_question="Q2?")
            ]
        )

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager
        )

        # Mock _teach_checkpoint 方法
        with patch.object(orchestrator, '_teach_checkpoint', new_callable=AsyncMock) as mock_teach:
            with patch.object(orchestrator, '_assign_homework', new_callable=AsyncMock) as mock_hw:
                with patch.object(orchestrator, '_collect_homework_and_feedback', new_callable=AsyncMock):
                    await orchestrator.run_autonomous_session()

                    # 验证调用了 2 次 _teach_checkpoint (每个检查点一次)
                    assert mock_teach.call_count == 2

                    # 验证最后一次调用了 _assign_homework
                    mock_hw.assert_called_once()

        asyncio.run(test())
```

### 步骤 2: 运行测试验证失败

```bash
pytest tests/units/test_session_orchestrator.py::test_run_autonomous_session_basic -v
```

Expected: FAIL - "SessionOrchestrator没有run_autonomous_session方法"

### 步骤 3: 实现最小代码

修改 `backend/models/session/orchestrator.py`，添加 run_autonomous_session 方法：

```python
"""SessionOrchestrator - 观察模式核心控制器."""

import asyncio
from typing import Callable

from agents.memories.memory_manager import MemoryManager
from agents.teacher_agent import TeacherAgent
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from agents.student_agent import StudentAgent


class SessionOrchestrator:
    """观察模式自动教学流程编排器.

    基于检查点系统驱动教学流程：
    - 遍历检查点数组
    - 协调教师和学生 agent 交互
    - 通过 WebSocket 推送状态更新
    - 集成 MemoryManager 记录教学过程
    """

    def __init__(
        self,
        *,
        teacher_agent: TeacherAgent,
        student_agents: list[StudentAgent],
        checkpoint_plan: CheckpointPlan,
        memory_manager: MemoryManager,
    ):
        """初始化编排器.

        Args:
            teacher_agent: 教师 agent
            student_agents: 学生 agent 列表
            checkpoint_plan: 检查点计划
            memory_manager: 记忆管理器
        """
        self.teacher_agent = teacher_agent
        self.student_agents = student_agents
        self.checkpoint_plan = checkpoint_plan
        self.memory_manager = memory_manager

        # WebSocket 推送回调（可选，用于测试）
        self._ws_push_callback: Callable | None = None

    def set_ws_push_callback(self, callback: Callable) -> None:
        """设置 WebSocket 推送回调（用于测试）."""
        self._ws_push_callback = callback

    async def run_autonomous_session(self) -> None:
        """运行自动教学会话（基于检查点）.

        遍历所有检查点，对每个检查点执行教学流程：
        - 灌输式: TEACHING → COMPLETE
        - 启发式/讨论式: TEACHING → QUESTIONS → COMPLETE

        最后一个检查点完成后布置作业和收集反馈。
        """
        num_checkpoints = len(self.checkpoint_plan.checkpoints)

        for i, checkpoint in enumerate(self.checkpoint_plan.checkpoints):
            # 更新当前索引
            self.checkpoint_plan.current_index = i

            # 教授当前检查点
            await self._teach_checkpoint(checkpoint)

        # 所有检查点完成后，布置作业和收集反馈
        await self._assign_homework()
        await self._collect_homework_and_feedback()

    async def _teach_checkpoint(self, checkpoint: Checkpoint) -> None:
        """教授单个检查点.

        Args:
            checkpoint: 当前检查点
        """
        # TEACHING 状态
        checkpoint.state = CheckpointState.TEACHING
        await self._ws_push_checkpoint_state(checkpoint)

        # 传授知识点
        await self._deliver_checkpoint_lecture(checkpoint)

        # 根据教学模式决定是否进入 QUESTIONS 状态
        mode = self.checkpoint_plan.teaching_mode

        if mode in ("heuristic", "discussion"):
            # QUESTIONS 状态
            checkpoint.state = CheckpointState.QUESTIONS
            await self._ws_push_checkpoint_state(checkpoint)

            # 处理学生互动
            await self._handle_checkpoint_questions(checkpoint)

        # COMPLETE 状态
        checkpoint.state = CheckpointState.COMPLETE
        await self._ws_push_checkpoint_state(checkpoint)

        # 记录知识点到 MemoryManager
        await self._trigger_observer_learning_for_checkpoint(checkpoint)

    async def _deliver_checkpoint_lecture(self, checkpoint: Checkpoint) -> None:
        """传授检查点知识点.

        Args:
            checkpoint: 当前检查点

        通过 TeacherAgentMemory 将 checkpoint.key_point 注入到教师 agent 的 system prompt，
        使教师专门讲授该知识点。
        """
        # 记录当前知识点到教师记忆
        self.memory_manager.teacher_memory.record_covered_topic(checkpoint.key_point)

        # 调用教师 agent 生成讲授内容
        lecture_content = await self.teacher_agent.generate_teaching_content()

        # 记录到会话记忆
        from schemas.message import Message, MessageType
        from datetime import datetime

        message = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content=lecture_content,
            receiver="all",
            timestamp=datetime.now()
        )

        self.memory_manager.process_message(message)

    async def _handle_checkpoint_questions(self, checkpoint: Checkpoint) -> None:
        """处理检查点问题环节.

        Args:
            checkpoint: 当前检查点

        启发式和讨论式模式下，教师提出 checkpoint_question，
        收集学生回答，并提供反馈。
        """
        # 教师提出检查点问题
        question_content = await self.teacher_agent.ask_checkpoint_question(
            checkpoint.checkpoint_question
        )

        # 记录问题到会话记忆
        from schemas.message import Message, MessageType
        from datetime import datetime

        message = Message(
            sender="teacher",
            message_type=MessageType.CHECKPOINT_QUESTION,
            content=question_content,
            receiver="all",
            timestamp=datetime.now()
        )

        self.memory_manager.process_message(message)

        # 收集学生回答
        await self._collect_student_answers()

    async def _collect_student_answers(self) -> None:
        """收集学生回答（场景 A: 教师提问）.

        教师提问后，学生基于 should_respond() 决定是否回答。
        如果无人回答，教师指定某个学生回答。
        """
        import random

        responding_students = []

        # 让每个学生决定是否响应
        for student in self.student_agents:
            if student.should_respond():
                responding_students.append(student)

        # 如果无人响应，随机指定一个学生
        if not responding_students:
            designated_student = random.choice(self.student_agents)
            await self._single_student_answer(designated_student)
        else:
            # 收集所有响应学生的回答
            for student in responding_students:
                answer = await student.answer_question("Please answer the question.")
                self._record_student_message(student.profile.name, answer)

    async def _single_student_answer(self, student: StudentAgent) -> None:
        """让被指定的学生回答.

        Args:
            student: 被指定的学生 agent
        """
        answer = await student.answer_question("Please answer the question.")
        self._record_student_message(student.profile.name, answer)

    def _record_student_message(self, student_name: str, content: str) -> None:
        """记录学生消息到记忆.

        Args:
            student_name: 学生名称
            content: 消息内容
        """
        from schemas.message import Message, MessageType
        from datetime import datetime

        message = Message(
            sender=student_name,
            message_type=MessageType.ANSWER_TO_CHECKPOINT,
            content=content,
            receiver="teacher",
            timestamp=datetime.now()
        )

        self.memory_manager.process_message(message)

    async def _trigger_observer_learning_for_checkpoint(self, checkpoint: Checkpoint) -> None:
        """检查点完成后触发旁听学习.

        Args:
            checkpoint: 已完成的检查点

        所有未参与对话的学生尝试从 checkpoint.key_point 中学习。
        """
        # 从 key_point 提取知识点（简化版本）
        knowledge_points = [checkpoint.key_point]

        for student in self.student_agents:
            # 尝试学习新知识
            student.memory.update_knowledge(
                knowledge_points,
                random.Random()  # 使用新的 random 实例
            )

    async def _ws_push_checkpoint_state(self, checkpoint: Checkpoint) -> None:
        """通过 WebSocket 推送检查点状态变更.

        Args:
            checkpoint: 当前检查点
        """
        if self._ws_push_callback:
            await self._ws_push_callback({
                "type": "checkpoint_state_change",
                "data": {
                    "index": self.checkpoint_plan.current_index,
                    "checkpoint": {
                        "title": checkpoint.title,
                        "state": checkpoint.state.value,
                        "key_point": checkpoint.key_point
                    },
                    "progress": {
                        "current": self.checkpoint_plan.current_index + 1,
                        "total": len(self.checkpoint_plan.checkpoints),
                        "completed": self.checkpoint_plan.current_index
                    }
                }
            })

    async def _assign_homework(self) -> None:
        """布置作业（只在最后一个检查点之后）.

        调用 TeacherAgent.assign_homework() 生成作业内容。
        """
        homework_content = await self.teacher_agent.assign_homework()

        # 记录到会话记忆
        from schemas.message import Message, MessageType
        from datetime import datetime

        message = Message(
            sender="teacher",
            message_type=MessageType.ASSIGN_HOMEWORK,
            content=homework_content,
            receiver="all",
            timestamp=datetime.now()
        )

        self.memory_manager.process_message(message)

    async def _collect_homework_and_feedback(self) -> None:
        """收集作业和反馈.

        1. 每个学生提交作业 (submit_homework)
        2. 教师评分作业 (grade_homework)
        3. 教师给出结束反馈 (end_feedback)
        4. 每个学生给出课程反馈 (give_feedback)
        """
        # 收集学生作业
        for student in self.student_agents:
            homework = await student.submit_homework("Complete your homework.")

            from schemas.message import Message, MessageType
            from datetime import datetime

            message = Message(
                sender=student.profile.name,
                message_type=MessageType.HOMEWORK_SUBMISSION,
                content=homework,
                receiver="teacher",
                timestamp=datetime.now()
            )

            self.memory_manager.process_message(message)

        # 教师评分作业
        for student in self.student_agents:
            # 获取学生最后提交的作业
            homeworks = [
                m for m in self.memory_manager.session_memory.messages
                if m.message_type == MessageType.HOMEWORK_SUBMISSION
                and m.sender == student.profile.name
            ]

            if homeworks:
                last_homework = homeworks[-1]
                feedback = await self.teacher_agent.grade_homework(
                    student.profile.name,
                    last_homework.content
                )

                from schemas.message import Message, MessageType
                from datetime import datetime

                message = Message(
                    sender="teacher",
                    message_type=MessageType.HOMEWORK_FEEDBACK,
                    content=feedback,
                    receiver=student.profile.name,
                    timestamp=datetime.now()
                )

                self.memory_manager.process_message(message)

        # 教师给出结束反馈
        end_feedback = await self.teacher_agent.end_feedback()

        from schemas.message import Message, MessageType
        from datetime import datetime

        message = Message(
            sender="teacher",
            message_type=MessageType.END_FEEDBACK,
            content=end_feedback,
            receiver="all",
            timestamp=datetime.now()
        )

        self.memory_manager.process_message(message)

        # 收集学生课程反馈
        for student in self.student_agents:
            feedback = await student.give_feedback("Provide your feedback on this course.")

            from schemas.message import Message, MessageType
            from datetime import datetime

            message = Message(
                sender=student.profile.name,
                message_type=MessageType.FEEDBACK_SUBMISSION,
                content=feedback,
                receiver="teacher",
                timestamp=datetime.now()
            )

            self.memory_manager.process_message(message)
```

### 步骤 4: 运行测试验证通过

```bash
pytest tests/units/test_session_orchestrator.py::test_run_autonomous_session_basic -v
```

Expected: PASS

### 步骤 5: 提交

```bash
git add backend/models/session/orchestrator.py backend/tests/units/test_session_orchestrator.py
git commit -m "feat: implement run_autonomous_session and checkpoint teaching flow"
```

---

## Task 4: 观察模式 Schemas

**Files:**
- Create: `backend/models/observation/schemas.py`
- Create: `backend/models/observation/__init__.py`
- Test: `backend/tests/units/test_observation_schemas.py`

### 步骤 1: 写失败的测试

```python
def test_observation_config_schema():
    """测试 ObservationConfig schema."""
    from models.observation.schemas import ObservationConfig
    from schemas.student import StudentProfile, StudentLevel, StudentAttitude

    config = ObservationConfig(
        topic="Python Basics",
        teaching_mode="heuristic",
        checkpoint_count=3,
        students=[
            StudentProfile(
                name="Student1",
                level=StudentLevel.AVERAGE,
                attitude=StudentAttitude.NEUTRAL
            )
        ]
    )

    assert config.topic == "Python Basics"
    assert config.teaching_mode == "heuristic"
    assert len(config.students) == 1


def test_observation_start_response_schema():
    """测试 ObservationStartResponse schema."""
    from models.observation.schemas import ObservationStartResponse

    response = ObservationStartResponse(
        session_id=1,
        status="running"
    )

    assert response.session_id == 1
    assert response.status == "running"
```

### 步骤 2: 运行测试验证失败

```bash
cd backend
pytest tests/units/test_observation_schemas.py -v
```

Expected: FAIL - "No module named 'models.observation.schemas'"

### 步骤 3: 实现最小代码

创建 `backend/models/observation/__init__.py`:

```python
"""Observation 模型包."""

from models.observation.schemas import (
    ObservationConfig,
    ObservationStartResponse,
    ObservationReport,
    ObservationMetrics,
)

__all__ = [
    "ObservationConfig",
    "ObservationStartResponse",
    "ObservationReport",
    "ObservationMetrics",
]
```

创建 `backend/models/observation/schemas.py`:

```python
"""观察模式 Pydantic schemas."""

from pydantic import BaseModel, Field

from schemas.student import StudentProfile


class ObservationConfig(BaseModel):
    """观察模式配置."""

    topic: str = Field(min_length=1, description="教学主题")
    teaching_mode: str = Field(description="教学模式 (didactic/heuristic/discussion)")
    checkpoint_count: int = Field(default=5, ge=1, le=10, description="检查点数量")
    students: list[StudentProfile] = Field(min_length=1, description="学生列表")


class ObservationStartResponse(BaseModel):
    """观察模式启动响应."""

    session_id: int = Field(description="会话ID")
    status: str = Field(description="会话状态")


class ObservationMetrics(BaseModel):
    """观察模式指标."""

    total_checkpoints: int = Field(description="总检查点数")
    completed_checkpoints: int = Field(description="已完成检查点数")
    total_messages: int = Field(description="总消息数")
    student_participation: dict[str, int] = Field(default_factory=dict, description="学生参与次数")


class ObservationReport(BaseModel):
    """观察模式报告."""

    session_id: int = Field(description="会话ID")
    topic: str = Field(description="教学主题")
    teaching_mode: str = Field(description="教学模式")
    metrics: ObservationMetrics = Field(description="教学指标")
    messages: list[str] = Field(description="消息摘要")
```

### 步骤 4: 运行测试验证通过

```bash
pytest tests/units/test_observation_schemas.py -v
```

Expected: PASS

### 步骤 5: 提交

```bash
git add backend/models/observation/ backend/tests/units/test_observation_schemas.py
git commit -m "feat: add observation mode schemas"
```

---

## Task 5: 观察模式 API 路由

**Files:**
- Create: `backend/models/observation/router.py`
- Test: `backend/tests/integration/test_observation_api.py`

### 步骤 1: 写失败的测试

```python
def test_start_observation_session():
    """测试启动观察模式会话."""
    import asyncio
    from fastapi.testclient import TestClient
    from unittest.mock import Mock, AsyncMock, patch

    from main import app

    async def test():
        # Mock CheckpointPlanService
        mock_plan = Mock()
        mock_plan.topic = "Test Topic"
        mock_plan.teaching_mode = "heuristic"
        mock_plan.checkpoints = []

        with patch("models.observation.router.CheckpointPlanService") as MockService:
            with patch("models.observation.router.SessionOrchestrator") as MockOrchestrator:
                with patch("models.observation.router.MemoryManager"):
                    mock_service_instance = Mock()
                    mock_service_instance.generate_plan = AsyncMock(return_value=mock_plan)
                    MockService.return_value = mock_service_instance

                    # Mock orchestrator
                    mock_orchestrator = Mock()
                    mock_orchestrator.run_autonomous_session = AsyncMock()
                    MockOrchestrator.return_value = mock_orchestrator

                    client = TestClient(app)

                    response = client.post(
                        "/observation/start",
                        json={
                            "topic": "Python Basics",
                            "teaching_mode": "heuristic",
                            "checkpoint_count": 3,
                            "students": [
                                {
                                    "name": "Student1",
                                    "level": "average",
                                    "attitude": "neutral"
                                }
                            ]
                        }
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert "session_id" in data
                    assert data["status"] == "running"

    asyncio.run(test())
```

### 步骤 2: 运行测试验证失败

```bash
cd backend
pytest tests/integration/test_observation_api.py::test_start_observation_session -v
```

Expected: FAIL - "404 Not Found"

### 步骤 3: 实现最小代码

创建 `backend/models/observation/router.py`:

```python
"""观察模式 API 路由."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.llm_client import create_llm_client
from models.checkpoint.service import CheckpointPlanService
from models.checkpoint.schemas import CheckpointPlan
from models.observation.schemas import (
    ObservationConfig,
    ObservationMetrics,
    ObservationReport,
    ObservationStartResponse,
)
from models.observation.router import router as observation_router
from models.session.orchestrator import SessionOrchestrator
from schemas.message import Message
from schemas.student import StudentProfile

router = APIRouter(prefix="/observation", tags=["observation"])


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    Args:
        config: 观察模式配置
        db: 数据库会话

    Returns:
        会话ID和状态
    """
    # 1. 创建教学会话记录
    from orm.teaching_session import TeachingSessionModel
    from datetime import datetime

    session_record = TeachingSessionModel(
        teaching_mode=config.teaching_mode,
        topic=config.topic,
        students_config=[s.model_dump() for s in config.students],
        status="running",
        start_time=datetime.now()
    )

    db.add(session_record)
    await db.commit()
    await db.refresh(session_record)

    session_id = session_record.id

    # 2. 生成检查点计划
    llm = create_llm_client()
    checkpoint_service = CheckpointPlanService(llm=llm)

    try:
        plan = await checkpoint_service.generate_plan(
            topic=config.topic,
            teaching_mode=config.teaching_mode,
            checkpoint_count=config.checkpoint_count
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid checkpoint plan generated: {e}"
        ) from e

    # 3. 保存检查点计划
    from models.checkpoint.persistence_service import CheckpointPlanPersistence

    persistence = CheckpointPlanPersistence(db)
    await persistence.save_plan(session_id=session_id, plan=plan)

    # 4. 创建 agents（后台运行）
    # TODO: 在后台任务中运行 orchestrator
    # 这里先返回 session_id，实际教学由单独的端点触发

    return ObservationStartResponse(
        session_id=session_id,
        status="running"
    )


@router.get("/{session_id}/report", summary="获取观察模式报告", response_model=ObservationReport)
async def get_observation_report(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ObservationReport:
    """获取观察模式会话报告.

    Args:
        session_id: 会话ID
        db: 数据库会话

    Returns:
        观察模式报告
    """
    # 1. 加载会话记录
    from orm.teaching_session import TeachingSessionModel
    from sqlalchemy import select

    result = await db.execute(
        select(TeachingSessionModel).where(TeachingSessionModel.id == session_id)
    )
    session_record = result.scalar_one_or_none()

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    # 2. 加载检查点计划
    from models.checkpoint.persistence_service import CheckpointPlanPersistence

    persistence = CheckpointPlanPersistence(db)
    plan = await persistence.load_plan(session_id=session_id)

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint plan for session {session_id} not found"
        )

    # 3. 计算已完成检查点数
    completed_count = sum(
        1 for cp in plan.checkpoints
        if cp.state.value in ("complete",)
    )

    # 4. 加载消息
    from orm.message import MessageModel
    from sqlalchemy import select

    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.timestamp)
    )
    message_records = result.scalars().all()

    # 5. 计算学生参与次数
    student_participation: dict[str, int] = {}
    for msg_record in message_records:
        sender = msg_record.sender
        if sender != "teacher":
            student_participation[sender] = student_participation.get(sender, 0) + 1

    # 6. 构建响应
    metrics = ObservationMetrics(
        total_checkpoints=len(plan.checkpoints),
        completed_checkpoints=completed_count,
        total_messages=len(message_records),
        student_participation=student_participation
    )

    messages = [f"{msg.sender}: {msg.content[:50]}..." for msg in message_records[:10]]

    return ObservationReport(
        session_id=session_id,
        topic=session_record.topic,
        teaching_mode=session_record.teaching_mode,
        metrics=metrics,
        messages=messages
    )
```

### 步骤 4: 运行测试验证通过

```bash
pytest tests/integration/test_observation_api.py::test_start_observation_session -v
```

Expected: PASS

### 步骤 5: 注册路由

修改 `backend/main.py` 添加 observation router：

```python
from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from models.checkpoint.router import router as checkpoint_router  # noqa: E402
from models.observation.router import router as observation_router  # noqa: E402

app = FastAPI()

app.include_router(checkpoint_router)
app.include_router(observation_router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 步骤 6: 提交

```bash
git add backend/models/observation/router.py backend/main.py backend/tests/integration/test_observation_api.py
git commit -m "feat: add observation mode API endpoints"
```

---

## Task 6: WebSocket 端点

**Files:**
- Create: `backend/models/session/router_websocket.py`
- Test: `backend/tests/integration/test_websocket.py`

### 步骤 1: 写失败的测试

```python
def test_websocket_checkpoint_state_change():
    """测试 WebSocket 检查点状态变更事件."""
    import asyncio
    from fastapi.testclient import TestClient
    from main import app

    async def test():
        with TestClient(app) as client:
            with client.websocket_connect("/ws/sessions/1") as websocket:
                # 接收连接确认消息
                data = websocket.receive_json()
                assert data["type"] == "connected"

                # 接收检查点状态变更
                data = websocket.receive_json()
                assert data["type"] == "checkpoint_state_change"
                assert "data" in data

    asyncio.run(test())
```

### 步骤 2: 运行测试验证失败

```bash
cd backend
pytest tests/integration/test_websocket.py::test_websocket_checkpoint_state_change -v
```

Expected: FAIL - "WebSocket endpoint not found"

### 步骤 3: 实现最小代码

创建 `backend/models/session/router_websocket.py`:

```python
"""Session WebSocket 路由."""

from typing import Annotated

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def websocket_session(
    session_id: int,
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """会话 WebSocket 端点.

    推送检查点状态变更事件：
    - checkpoint_state_change: 检查点状态变更

    Args:
        session_id: 会话ID
        websocket: WebSocket 连接
        db: 数据库会话
    """
    await websocket.accept()

    # 发送连接确认
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id
    })

    try:
        # TODO: 实现实际的消息推送逻辑
        # 这里需要从某个地方获取状态更新并推送
        # 可以使用 asyncio.Queue 或者数据库轮询

        while True:
            # 等待消息（实际实现中，这里会从队列接收）
            try:
                # 模拟接收消息（实际实现需要）
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    except WebSocketDisconnect:
        pass
    finally:
        # 清理资源
        pass
```

### 步骤 4: 注册 WebSocket 路由

修改 `backend/main.py` 添加 websocket router：

```python
from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from models.checkpoint.router import router as checkpoint_router  # noqa: E402
from models.observation.router import router as observation_router  # noqa: E402
from models.session.router_websocket import router as websocket_router  # noqa: E402

app = FastAPI()

app.include_router(checkpoint_router)
app.include_router(observation_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 步骤 5: 运行测试验证通过

```bash
pytest tests/integration/test_websocket.py::test_websocket_checkpoint_state_change -v
```

Expected: PASS

### 步骤 6: 提交

```bash
git add backend/models/session/router_websocket.py backend/main.py backend/tests/integration/test_websocket.py
git commit -m "feat: add session websocket endpoint"
```

---

## Task 7: 集成测试 - 完整流程

**Files:**
- Create: `backend/tests/integration/test_session_orchestrator_full.py`

### 步骤 1: 写测试

```python
"""SessionOrchestrator 完整流程集成测试.

包含两种测试：
1. mock LLM 版本 - 快速验证流程逻辑
2. 真实 LLM 版本 - 展示完整课堂过程（带控制台输出）
"""

import asyncio  # noqa: E402
import pytest  # noqa: E402

def test_full_observation_session():
    """测试完整的观察模式会话流程 (使用 mock LLM)."""
    from agents.memories import SessionMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.teacher_agent import TeacherAgent
    from agents.student_agent import StudentAgent
    from models.checkpoint.schemas import CheckpointPlan, Checkpoint, CheckpointState
    from models.session.orchestrator import SessionOrchestrator
    from schemas.student import StudentProfile, StudentLevel, StudentAttitude
    from unittest.mock import Mock, AsyncMock

    async def test():
        # Mock LLM
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value="Test response")

        # 创建 session
        session_memory = SessionMemory(topic="Python Basics")
        memory_manager = MemoryManager(session_memory=session_memory)

        # 创建 teacher
        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=mock_llm,
            teaching_mode="heuristic",
            memory_manager=memory_manager
        )

        # 创建学生
        student_profile = StudentProfile(
            name="TestStudent",
            level=StudentLevel.AVERAGE,
            attitude=StudentAttitude.ACTIVE
        )

        student = StudentAgent(
            session_memory=session_memory,
            llm=mock_llm,
            profile=student_profile
        )

        # 创建检查点计划（2个检查点）
        plan = CheckpointPlan(
            topic="Python Basics",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="Variables",
                    key_point="Python variables store data",
                    checkpoint_question="What is a variable?"
                ),
                Checkpoint(
                    title="Data Types",
                    key_point="Python has several data types",
                    checkpoint_question="Name some Python data types."
                )
            ]
        )

        # 创建 orchestrator
        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager
        )

        # 记录 WebSocket 推送
        ws_messages = []

        async def ws_callback(msg):
            ws_messages.append(msg)

        orchestrator.set_ws_push_callback(ws_callback)

        # 运行会话
        await orchestrator.run_autonomous_session()

        # 验证检查点状态
        assert plan.checkpoints[0].state == CheckpointState.COMPLETE
        assert plan.checkpoints[1].state == CheckpointState.COMPLETE

        # 验证 WebSocket 推送
        assert len(ws_messages) > 0

        # 验证消息记录
        assert len(session_memory.messages) > 0

        # 验证教师记忆
        assert len(memory_manager.teacher_memory.covered_topics) > 0

    asyncio.run(test())


@pytest.mark.integration
def test_full_observation_session_with_console_output():
    """测试完整的观察模式会话流程，带控制台输出 (使用真实 LLM).

    此测试展示完整的课堂过程，包括：
    - 教师讲授每个检查点
    - 教师提问和学生回答
    - 布置作业和收集反馈
    - 所有过程输出到控制台

    运行方式: pytest tests/integration/test_session_orchestrator_full.py::test_full_observation_session_with_console_output -v -s -m integration
    """
    import asyncio
    from datetime import datetime
    from agents.memories import SessionMemory, TeacherAgentMemory, StudentAgentMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.teacher_agent import TeacherAgent
    from agents.student_agent import StudentAgent
    from models.checkpoint.service import CheckpointPlanService
    from models.checkpoint.schemas import CheckpointPlan
    from models.session.orchestrator import SessionOrchestrator
    from schemas.student import StudentProfile, StudentLevel, StudentAttitude
    from core.llm_client import LLMClient

    async def test():
        # 使用真实 LLM
        llm = LLMClient.from_config()

        # 创建 session
        session_id = 9999  # 使用固定 session_id 便于测试
        session_memory = SessionMemory(session_id=session_id, topic="Python 变量基础")
        teacher_memory = TeacherAgentMemory()

        # 创建学生（3 个学生，不同水平）
        students = []
        student_configs = [
            ("张三", StudentLevel.EXCELLENT, StudentAttitude.ACTIVE),
            ("李四", StudentLevel.AVERAGE, StudentAttitude.NEUTRAL),
            ("王五", StudentLevel.BEGINNER, StudentAttitude.PASSIVE),
        ]

        for name, level, attitude in student_configs:
            profile = StudentProfile(name=name, level=level, attitude=attitude)
            student_memory = StudentAgentMemory.from_profile(profile)
            student = StudentAgent(
                session_memory=session_memory,
                llm=llm,
                profile=profile,
                memory=student_memory
            )
            students.append(student)

        # 创建教师
        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=llm,
            teaching_mode="heuristic",
            memory=teacher_memory
        )

        # 创建 MemoryManager
        memory_manager = MemoryManager(session_memory=session_memory)
        memory_manager.teacher_memory = teacher_memory
        for student in students:
            memory_manager.student_memories[student.profile.name] = student.memory

        # 生成检查点计划（使用真实 LLM）
        print(f"\n{'=' * 70}")
        print(f"【观察模式集成测试】主题: Python 变量基础")
        print(f"教学模式: 启发式 (heuristic)")
        print(f"学生数量: {len(students)}")
        print(f"{'=' * 70}\n")

        checkpoint_service = CheckpointPlanService(llm=llm)
        plan = await checkpoint_service.generate_plan(
            topic="Python 变量基础",
            teaching_mode="heuristic",
            checkpoint_count=2
        )

        print(f"生成的检查点计划:")
        print(f"  主题: {plan.topic}")
        print(f"  教学模式: {plan.teaching_mode}")
        print(f"  检查点数量: {len(plan.checkpoints)}")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"    检查点 {i}: {cp.title}")
        print(f"\n{'=' * 70}")
        print(f"【开始上课】")
        print(f"{'=' * 70}\n")

        # 创建 orchestrator
        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=students,
            checkpoint_plan=plan,
            memory_manager=memory_manager
        )

        # 设置 WebSocket 推送回调（打印状态变更）
        async def ws_callback(msg):
            if msg.get("type") == "checkpoint_state_change":
                data = msg["data"]
                checkpoint = data["checkpoint"]
                state = checkpoint["state"]
                print(f"[WebSocket] 检查点状态变更: {checkpoint['title']} → {state}")

        orchestrator.set_ws_push_callback(ws_callback)

        # 运行完整会话
        await orchestrator.run_autonomous_session()

        print(f"\n{'=' * 70}")
        print(f"【课程结束】")
        print(f"{'=' * 70}")

        # 打印课程统计
        print(f"\n课程统计:")
        print(f"  总消息数: {len(session_memory.messages)}")
        print(f"  教师讲授主题: {len(teacher_memory.covered_topics)}")
        print(f"  学生参与情况:")
        for student in students:
            participation = teacher_memory.student_participation.get(student.profile.name, 0)
            print(f"    {student.profile.name}: {participation} 次参与")

        # 打印最后几条消息
        print(f"\n最后几条消息:")
        for msg in session_memory.messages[-5:]:
            sender = msg.sender
            msg_type = msg.message_type.value
            content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
            print(f"  [{sender}] ({msg_type}): {content}")

        print(f"\n{'=' * 70}\n")

        # 验证
        assert len(session_memory.messages) > 0
        assert len(teacher_memory.covered_topics) > 0
        for cp in plan.checkpoints:
            assert cp.state == CheckpointState.COMPLETE

    asyncio.run(test())


@pytest.mark.integration
def test_multi_student_classroom():
    """测试多学生课堂完整流程，带详细控制台输出 (使用真实 LLM).

    模拟 5 个学生在一个课堂中，展示：
    - 不同学生基于 should_respond() 概率决定是否回答
    - 优秀学生更活跃，初学者更被动
    - 教师对不同学生的作业给出不同评价
    - 每个学生的作业和反馈都有独立记录

    运行方式: pytest tests/integration/test_session_orchestrator_full.py::test_multi_student_classroom -v -s -m integration
    """
    import asyncio
    from datetime import datetime
    from agents.memories import SessionMemory, TeacherAgentMemory, StudentAgentMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.teacher_agent import TeacherAgent
    from agents.student_agent import StudentAgent
    from models.checkpoint.service import CheckpointPlanService
    from models.checkpoint.schemas import CheckpointPlan
    from models.session.orchestrator import SessionOrchestrator
    from schemas.student import StudentProfile, StudentLevel, StudentAttitude
    from schemas.message import MessageType
    from core.llm_client import LLMClient

    async def test():
        llm = LLMClient.from_config()

        # 创建 session
        session_id = 8888
        session_memory = SessionMemory(session_id=session_id, topic="Python 条件语句与循环")
        teacher_memory = TeacherAgentMemory()

        # 创建 5 个学生，模拟真实课堂的多样性
        student_configs = [
            ("赵学霸", StudentLevel.EXCELLENT, StudentAttitude.ACTIVE),
            ("钱积极", StudentLevel.ABOVE_AVERAGE, StudentAttitude.ACTIVE),
            ("孙普通", StudentLevel.AVERAGE, StudentAttitude.NEUTRAL),
            ("李沉默", StudentLevel.AVERAGE, StudentAttitude.PASSIVE),
            ("周小白", StudentLevel.BEGINNER, StudentAttitude.PASSIVE),
        ]

        students = []
        for name, level, attitude in student_configs:
            profile = StudentProfile(name=name, level=level, attitude=attitude)
            student_memory = StudentAgentMemory.from_profile(profile)
            student = StudentAgent(
                session_memory=session_memory,
                llm=llm,
                profile=profile,
                memory=student_memory
            )
            students.append(student)

        # 创建教师
        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=llm,
            teaching_mode="heuristic",
            memory=teacher_memory
        )

        # 创建 MemoryManager
        memory_manager = MemoryManager(session_memory=session_memory)
        memory_manager.teacher_memory = teacher_memory
        for student in students:
            memory_manager.student_memories[student.profile.name] = student.memory

        # 打印课堂信息
        print(f"\n{'#' * 70}")
        print(f"  多学生课堂集成测试")
        print(f"{'#' * 70}")
        print(f"  主题: {session_memory.topic}")
        print(f"  教学模式: 启发式 (heuristic)")
        print(f"  学生列表:")
        for s in students:
            level_str = s.profile.level.value
            attitude_str = s.profile.attitude.value
            print(f"    - {s.profile.name} (水平: {level_str}, 态度: {attitude_str})")
        print(f"{'#' * 70}\n")

        # 生成检查点计划（3 个检查点）
        print("[1/4] 生成检查点计划...")
        checkpoint_service = CheckpointPlanService(llm=llm)
        plan = await checkpoint_service.generate_plan(
            topic=session_memory.topic,
            teaching_mode="heuristic",
            checkpoint_count=3
        )

        print(f"  生成 {len(plan.checkpoints)} 个检查点:")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"    {i}. {cp.title} - {cp.key_point}")
        print()

        # 创建 orchestrator
        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=students,
            checkpoint_plan=plan,
            memory_manager=memory_manager
        )

        # WebSocket 推送回调
        async def ws_callback(msg):
            if msg.get("type") == "checkpoint_state_change":
                data = msg["data"]
                checkpoint = data["checkpoint"]
                progress = data["progress"]
                print(
                    f"  [进度 {progress['current']}/{progress['total']}] "
                    f"检查点「{checkpoint['title']}」 → {checkpoint['state']}"
                )

        orchestrator.set_ws_push_callback(ws_callback)

        # 运行完整会话
        print("[2/4] 开始教学流程...\n")
        await orchestrator.run_autonomous_session()

        # 打印完整课堂记录
        print(f"\n[3/4] 课堂记录:\n")

        # 按消息类型分组统计
        msg_by_type: dict[str, list] = {}
        for msg in session_memory.messages:
            t = msg.message_type.value
            msg_by_type.setdefault(t, []).append(msg)

        print(f"  消息类型统计:")
        for msg_type, msgs in msg_by_type.items():
            print(f"    {msg_type}: {len(msgs)} 条")

        # 按学生统计参与情况
        print(f"\n  学生参与统计:")
        for student in students:
            name = student.profile.name
            student_msgs = [m for m in session_memory.messages if m.sender == name]
            participation = teacher_memory.student_participation.get(name, 0)
            learned = len(student.memory.learned_concepts)
            print(f"    {name}:")
            print(f"      发言次数: {len(student_msgs)}")
            print(f"      参与记录: {participation}")
            print(f"      学到知识点: {learned}")

        # 打印完整消息流
        print(f"\n  完整消息流:")
        print(f"  {'-' * 66}")
        for i, msg in enumerate(session_memory.messages, 1):
            sender = msg.sender
            msg_type = msg.message_type.value
            content = msg.content
            # 截断过长内容
            if len(content) > 80:
                content = content[:77] + "..."
            print(f"  {i:2d}. [{sender:6s}] ({msg_type:22s}) {content}")
        print(f"  {'-' * 66}")

        # 打印作业统计
        print(f"\n[4/4] 作业统计:\n")
        homework_msgs = msg_by_type.get("homework_submission", [])
        feedback_msgs = msg_by_type.get("homework_feedback", [])

        print(f"  作业提交: {len(homework_msgs)} 份")
        for hw in homework_msgs:
            content = hw.content[:50] + "..." if len(hw.content) > 50 else hw.content
            print(f"    [{hw.sender}] {content}")

        print(f"\n  作业反馈: {len(feedback_msgs)} 份")
        for fb in feedback_msgs:
            receiver = fb.receiver
            content = fb.content[:50] + "..." if len(fb.content) > 50 else fb.content
            print(f"    [教师→{receiver}] {content}")

        # 学生课程反馈
        course_feedback = msg_by_type.get("feedback_submission", [])
        print(f"\n  学生课程反馈: {len(course_feedback)} 份")
        for cf in course_feedback:
            content = cf.content[:50] + "..." if len(cf.content) > 50 else cf.content
            print(f"    [{cf.sender}] {content}")

        print(f"\n{'#' * 70}")
        print(f"  课堂结束 - 共 {len(session_memory.messages)} 条消息")
        print(f"{'#' * 70}\n")

        # 验证
        assert len(session_memory.messages) > 0
        assert len(teacher_memory.covered_topics) > 0
        for cp in plan.checkpoints:
            assert cp.state == CheckpointState.COMPLETE
        # 验证每个学生至少有记忆更新
        for student in students:
            assert student.memory is not None

    asyncio.run(test())
```

### 步骤 2: 运行测试

```bash
cd backend

# 运行 mock LLM 版本测试（快速）
pytest tests/integration/test_session_orchestrator_full.py::test_full_observation_session -v -s

# 运行真实 LLM 单学生版（带控制台输出）
pytest tests/integration/test_session_orchestrator_full.py::test_full_observation_session_with_console_output -v -s -m integration

# 运行真实 LLM 多学生课堂版（完整课堂模拟）
pytest tests/integration/test_session_orchestrator_full.py::test_multi_student_classroom -v -s -m integration
```

Expected: PASS

**说明**：
- `test_full_observation_session` - 使用 mock LLM，快速验证流程逻辑
- `test_full_observation_session_with_console_output` - 使用真实 LLM，3 个学生，展示完整课堂过程
- `test_multi_student_classroom` - 使用真实 LLM，**5 个学生**，模拟真实课堂多样性：
  - 不同水平（优秀/良好/中等/中等/初学者）
  - 不同态度（积极/积极/中性/被动/被动）
  - 完整消息流（带编号的时间线）
  - 按消息类型分组统计
  - 每个学生的参与次数和学到知识点数
  - 作业提交和反馈的独立记录
  - 学生课程反馈收集

### 步骤 3: 提交

```bash
git add backend/tests/integration/test_session_orchestrator_full.py
git commit -m "test: add full observation session integration test"
```

---

## Task 8: 验收测试

**Files:**
- Modify: `backend/tests/integration/test_session_orchestrator_full.py`

### 步骤 1: 添加验收测试

```python
def test_acceptance_criteria():
    """验收标准：能自动运行完整教学流程."""
    import asyncio
    from agents.memories import SessionMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.teacher_agent import TeacherAgent
    from agents.student_agent import StudentAgent
    from models.checkpoint.schemas import CheckpointPlan, Checkpoint
    from models.session.orchestrator import SessionOrchestrator
    from schemas.student import StudentProfile, StudentLevel, StudentAttitude
    from unittest.mock import Mock, AsyncMock

    async def test():
        # Mock LLM
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value="Test content")

        session_memory = SessionMemory(topic="Test")
        memory_manager = MemoryManager(session_memory=session_memory)

        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=memory_manager
        )

        student = StudentAgent(
            session_memory=session_memory,
            llm=mock_llm,
            profile=StudentProfile(
                name="S1",
                level=StudentLevel.AVERAGE,
                attitude=StudentAttitude.NEUTRAL
            )
        )

        plan = CheckpointPlan(
            topic="Test",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(title="CP1", key_point="P1", checkpoint_question="Q1?"),
                Checkpoint(title="CP2", key_point="P2", checkpoint_question="Q2?")
            ]
        )

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager
        )

        ws_messages = []
        orchestrator.set_ws_push_callback(lambda msg: ws_messages.append(msg))

        await orchestrator.run_autonomous_session()

        # 验收标准 1: 能自动运行完整教学流程
        assert plan.checkpoints[0].state.value == "complete"
        assert plan.checkpoints[1].state.value == "complete"

        # 验收标准 2: 遍历完所有检查点后自动结束
        assert orchestrator.checkpoint_plan.current_index == 1

        # 验收标准 3: 灌输式跳过 QUESTIONS 状态
        # 灌输式应该直接 TEACHING → COMPLETE
        # 验证没有 QUESTIONS 状态的 WebSocket 消息
        teaching_states = [
            msg["data"]["checkpoint"]["state"]
            for msg in ws_messages
            if msg["type"] == "checkpoint_state_change"
        ]
        assert "questions" not in teaching_states

        # 验收标准 4: 检查点状态变更通过 WebSocket 实时推送
        assert len(ws_messages) > 0

        # 验收标准 5: 能布置作业
        hw_messages = [
            msg for msg in session_memory.messages
            if hasattr(msg, 'message_type') and msg.message_type.value == "assign_homework"
        ]
        assert len(hw_messages) > 0

    asyncio.run(test())
```

### 步骤 2: 运行测试

```bash
pytest tests/integration/test_session_orchestrator_full.py::test_acceptance_criteria -v -s
```

Expected: PASS

### 步骤 3: 提交

```bash
git add backend/tests/integration/test_session_orchestrator_full.py
git commit -m "test: add acceptance criteria tests for SessionOrchestrator"
```

---

## Task 9: 运行所有测试

### 步骤 1: 运行全部测试

```bash
cd backend

# 单元测试
pytest tests/units/ -v

# 集成测试
pytest tests/integration/ -v

# 全部测试
pytest tests/ -v
```

Expected: 全部 PASS

### 步骤 2: 代码检查

```bash
ruff check .
ruff format .
```

### 步骤 3: 提交

```bash
git add .
git commit -m "chore: run all tests and format code"
```

---

## 真实 LLM 调用统计

本计划文档中，以下位置会调用真实 LLM（不包括测试中的 mock）：

### SessionOrchestrator 类中的 LLM 调用

| 位置 (行号) | 方法 | 调用 | 说明 |
|-----------|------|------|------|
| ~491 | `_teach_checkpoint()` | `teacher_agent.generate_teaching_content()` | 教师生成讲授内容 |
| ~517 | `_handle_checkpoint_questions()` | `teacher_agent.ask_checkpoint_question()` | 教师提出检查点问题 |
| ~560 | `_collect_student_answers()` | `student.answer_question()` | 学生回答问题（每个响应学生） |
| ~569 | `_single_student_answer()` | `student.answer_question()` | 被指定学生回答问题 |
| ~639 | `_assign_homework()` | `teacher_agent.assign_homework()` | 教师布置作业 |
| ~665 | `_collect_homework_and_feedback()` | `student.submit_homework()` | 学生提交作业（每个学生） |
| ~691 | `_collect_homework_and_feedback()` | `teacher_agent.grade_homework()` | 教师评分作业（每个学生） |
| ~710 | `_collect_homework_and_feedback()` | `teacher_agent.end_feedback()` | 教师结束反馈 |
| ~727 | `_collect_homework_and_feedback()` | `student.give_feedback()` | 学生课程反馈（每个学生） |

### 观察模式 API 中的 LLM 调用

| 位置 (行号) | 端点 | 调用 | 说明 |
|-----------|------|------|------|
| ~1038 | `POST /observation/start` | `checkpoint_service.generate_plan()` | 生成检查点计划 |

### 统计汇总

- **总计**: 10 个不同的 LLM 调用点
- **SessionOrchestrator 内部**: 9 个调用点
- **API 层**: 1 个调用点（检查点计划生成）

**注意**：其中部分调用在循环中执行（如 `grade_homework`、`submit_homework`、`give_feedback` 对每个学生执行一次），实际运行时的 LLM 调用次数会根据学生数量而变化。

---

## 完成检查清单

在实施完成后，验证以下内容：

- [ ] Message schema 添加了 receiver 字段
- [ ] SessionOrchestrator 类实现完成
- [ ] run_autonomous_session() 基于检查点迭代
- [ ] 检查点状态机 (PENDING → TEACHING → QUESTIONS → COMPLETE) 正确实现
- [ ] 灌输式模式跳过 QUESTIONS 状态
- [ ] WebSocket 推送检查点状态变更
- [ ] 观察模式 API 端点 (POST /observation/start, GET /observation/{id}/report)
- [ ] 所有测试通过 (单元 + 集成)
- [ ] 代码通过 ruff 检查

---

## 验收标准

基于 development-roadmap.md 中的验收标准：

- [ ] 能自动运行完整教学流程（基于检查点）
- [ ] 遍历完所有检查点后自动结束
- [ ] 灌输式跳过 QUESTIONS 状态
- [ ] 检查点状态变更通过 WebSocket 实时推送
- [ ] 能布置作业和收集反馈（最后一个检查点之后）
- [ ] 双方均可结束对话（至少一轮完成后）
- [ ] 旁听学生概率性学习触发
- [ ] 检查点完成后 key_point 记录到 MemoryManager
- [ ] 验证：创建观察会话，自动运行到结束

---

## 下一步

完成 Phase 7 后，继续 Phase 7.5: TeacherSessionController（教师模式核心）。

Phase 7.5 将实现：
- 教师模式手动控制教学流程
- 检查点编辑接口
- 手动推进检查点
- 场景 A/B 对话循环的完整实现
- 强制结束当前对话的逻辑

---

**实施顺序建议：**

1. 先完成 Task 1-3（Message Schema 扩展 + SessionOrchestrator 核心）
2. 再完成 Task 4-6（观察模式 API + WebSocket）
3. 最后完成 Task 7-9（集成测试 + 验收）

每个任务都遵循 TDD 流程：写失败测试 → 实现最小代码 → 验证通过 → 提交。
