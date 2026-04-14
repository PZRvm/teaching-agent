# 检查点级上下文隔离 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在每个检查点完成后生成 LLM 摘要并清除消息历史，解决教师 Agent 上下文溢出问题。

**Architecture:** SessionMemory 新增 `checkpoint_summaries` 列表存储跨检查点摘要。MemoryManager 新增 `summarize_checkpoint()` 方法在检查点边界调用 LLM 生成摘要并重置 message_history。TeacherAgent.end_feedback() 使用 `get_full_context()` 读取累积摘要替代原始消息。

**Tech Stack:** Python 3.12+, SQLAlchemy ORM, Alembic, pytest, unittest.mock

---

## 文件结构映射

| 文件 | 职责 | 改动类型 |
|------|------|----------|
| `backend/agents/memories/session_memory.py` | 会话记忆数据类 | 修改：新增字段和方法 |
| `backend/agents/memories/memory_manager.py` | 记忆管理器 | 修改：新增 summarize_checkpoint() |
| `backend/agents/teacher_agent.py` | 教师 Agent | 修改：end_feedback() 使用轻量上下文 |
| `backend/models/session/services/observation_service.py` | 观察模式编排器 | 修改：检查点边界调用摘要 |
| `backend/models/session/services/teacher_service.py` | 教师模式控制器 | 修改：检查点推进时调用摘要 |
| `backend/orm/session_memory.py` | 会话记忆 ORM | 修改：新增 JSON 列 |
| `backend/agents/memories/memory_persistence.py` | 记忆持久化 | 修改：save/load checkpoint_summaries |
| `backend/tests/units/test_memory_manager.py` | MemoryManager 测试 | 修改：新增测试 |
| `backend/tests/unit_llm/test_teacher_agent.py` | TeacherAgent 测试 | 修改：新增测试 |
| `backend/tests/unit_llm/test_session_orchestrator.py` | 编排器测试 | 修改：新增测试 |

---

### Task 1: SessionMemory 新增 checkpoint_summaries 字段

**Files:**
- Modify: `backend/agents/memories/session_memory.py`
- Test: `backend/tests/units/test_memory_manager.py`

- [ ] **Step 1: 写失败测试 — checkpoint_summaries 默认值**

在 `backend/tests/units/test_memory_manager.py` 的 `TestSessionMemory` 类末尾追加：

```python
    def test_init_checkpoint_summaries_default(self):
        """测试 checkpoint_summaries 默认为空列表."""
        from agents.memories.session_memory import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")

        assert hasattr(memory, "checkpoint_summaries")
        assert memory.checkpoint_summaries == []
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestSessionMemory::test_init_checkpoint_summaries_default -v`
Expected: FAIL — `AttributeError: 'SessionMemory' object has no attribute 'checkpoint_summaries'`

- [ ] **Step 3: 实现最小代码**

在 `backend/agents/memories/session_memory.py` 的 `SessionMemory` dataclass 中，在 `teaching_summary` 字段之后新增：

```python
    checkpoint_summaries: list[str] = field(default_factory=list)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestSessionMemory::test_init_checkpoint_summaries_default -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd backend && git add agents/memories/session_memory.py tests/units/test_memory_manager.py
git commit -m "feat(session-memory): 新增 checkpoint_summaries 字段"
```

---

### Task 2: SessionMemory 新增 clear_message_history() 方法

**Files:**
- Modify: `backend/agents/memories/session_memory.py`
- Test: `backend/tests/units/test_memory_manager.py`

- [ ] **Step 1: 写失败测试 — clear_message_history 清空消息和重置计数器**

```python
class TestSessionMemoryClearHistory:
    """SessionMemory.clear_message_history() 测试."""

    def test_clear_message_history_empties_list(self):
        """测试 clear_message_history 清空消息列表."""
        from agents.memories.session_memory import SessionMemory
        from models.session.schemas import Message, MessageType

        memory = SessionMemory(session_id=1, topic="Python基础")
        msg = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="变量是存储数据的容器",
            receiver="all",
        )
        memory.add_message(msg)

        assert len(memory.message_history) == 1

        memory.clear_message_history()

        assert memory.message_history == []

    def test_clear_message_history_resets_last_summary_update(self):
        """测试 clear_message_history 重置 last_summary_update."""
        from agents.memories.session_memory import SessionMemory
        from models.session.schemas import Message, MessageType

        memory = SessionMemory(session_id=1, topic="Python基础")
        memory.last_summary_update = 5

        memory.clear_message_history()

        assert memory.last_summary_update == 0

    def test_clear_message_history_preserves_checkpoint_summaries(self):
        """测试 clear_message_history 不影响 checkpoint_summaries."""
        from agents.memories.session_memory import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        memory.checkpoint_summaries = ["检查点1摘要"]

        memory.clear_message_history()

        assert memory.checkpoint_summaries == ["检查点1摘要"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestSessionMemoryClearHistory -v`
Expected: FAIL — `AttributeError: 'SessionMemory' object has no attribute 'clear_message_history'`

- [ ] **Step 3: 实现最小代码**

在 `backend/agents/memories/session_memory.py` 的 `SessionMemory` 类中，在 `mark_summary_updated()` 方法之后新增：

```python
    def clear_message_history(self) -> None:
        """清除消息历史（检查点边界调用）.

        同时将 last_summary_update 设为 0，因为新的检查点
        消息计数从 0 开始。
        """
        self.message_history.clear()
        self.last_summary_update = 0
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestSessionMemoryClearHistory -v`
Expected: PASS

- [ ] **Step 5: 运行全部 SessionMemory 测试确保无回归**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestSessionMemory -v`
Expected: 全部 PASS

- [ ] **Step 6: 提交**

```bash
cd backend && git add agents/memories/session_memory.py tests/units/test_memory_manager.py
git commit -m "feat(session-memory): 新增 clear_message_history() 方法"
```

---

### Task 3: SessionMemory 新增 get_full_context() 方法

**Files:**
- Modify: `backend/agents/memories/session_memory.py`
- Test: `backend/tests/units/test_memory_manager.py`

- [ ] **Step 1: 写失败测试 — get_full_context 包含检查点摘要**

```python
class TestSessionMemoryGetFullContext:
    """SessionMemory.get_full_context() 测试."""

    def test_get_full_context_includes_topic(self):
        """测试 get_full_context 包含教学主题."""
        from agents.memories.session_memory import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python变量")

        context = memory.get_full_context()

        assert "Python变量" in context

    def test_get_full_context_includes_checkpoint_summaries(self):
        """测试 get_full_context 包含检查点摘要."""
        from agents.memories.session_memory import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python变量")
        memory.checkpoint_summaries = [
            "讲授了变量和类型，学生理解良好",
            "讲授了列表和元组，部分学生困惑",
        ]

        context = memory.get_full_context()

        assert "讲授了变量和类型" in context
        assert "讲授了列表和元组" in context

    def test_get_full_context_includes_teaching_summary(self):
        """测试 get_full_context 包含教学摘要."""
        from agents.memories.session_memory import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python变量")
        memory.teaching_summary = "已讲授变量、列表"

        context = memory.get_full_context()

        assert "已讲授变量、列表" in context

    def test_get_full_context_includes_recent_messages(self):
        """测试 get_full_context 包含最近消息."""
        from agents.memories.session_memory import SessionMemory
        from models.session.schemas import Message, MessageType

        memory = SessionMemory(session_id=1, topic="Python变量")
        msg = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="变量是存储数据的容器",
            receiver="all",
        )
        memory.add_message(msg)

        context = memory.get_full_context()

        assert "变量是存储数据的容器" in context

    def test_get_full_context_empty_state(self):
        """测试空状态下的 get_full_context."""
        from agents.memories.session_memory import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python变量")

        context = memory.get_full_context()

        assert "教学主题: Python变量" in context
        assert "最近的对话:" in context
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestSessionMemoryGetFullContext -v`
Expected: FAIL — `AttributeError: 'SessionMemory' object has no attribute 'get_full_context'`

- [ ] **Step 3: 实现最小代码**

在 `backend/agents/memories/session_memory.py` 的 `SessionMemory` 类中，在 `get_agent_context()` 方法之后新增：

```python
    def get_full_context(self) -> str:
        """获取完整上下文（包含所有检查点摘要）.

        用于最终总结等需要全局视角的场景。
        包含 teaching_summary（如果有）和所有 checkpoint_summaries。
        """
        parts = [f"教学主题: {self.topic}"]
        if self.teaching_summary:
            parts.append(f"教学摘要: {self.teaching_summary}")
        if self.checkpoint_summaries:
            parts.append("各检查点教学摘要:")
            for i, summary in enumerate(self.checkpoint_summaries, 1):
                parts.append(f"  检查点{i}: {summary}")
        parts.append("最近的对话:")
        for msg in self.message_history[-self.max_history_messages:]:
            parts.append(f"[{msg.sender}] ({msg.message_type.value}): {msg.content}")
        return "\n".join(parts)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestSessionMemoryGetFullContext -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd backend && git add agents/memories/session_memory.py tests/units/test_memory_manager.py
git commit -m "feat(session-memory): 新增 get_full_context() 方法"
```

---

### Task 4: MemoryManager 新增 summarize_checkpoint() 方法

**Files:**
- Modify: `backend/agents/memories/memory_manager.py`
- Test: `backend/tests/units/test_memory_manager.py`

- [ ] **Step 1: 写失败测试 — summarize_checkpoint 基本行为**

```python
class TestMemoryManagerSummarizeCheckpoint:
    """MemoryManager.summarize_checkpoint() 测试."""

    def test_summarize_checkpoint_appends_summary(self):
        """测试 summarize_checkpoint 将摘要追加到 checkpoint_summaries."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory
        from models.session.schemas import Message, MessageType

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        session_mem.add_message(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量是存储数据的容器",
                receiver="all",
            )
        )

        mock_summary_fn = lambda p: "讲授了变量，学生理解良好"
        manager = MemoryManager(session_memory=session_mem, summary_fn=mock_summary_fn)

        result = manager.summarize_checkpoint()

        assert result == "讲授了变量，学生理解良好"
        assert session_mem.checkpoint_summaries == ["讲授了变量，学生理解良好"]

    def test_summarize_checkpoint_clears_message_history(self):
        """测试 summarize_checkpoint 清空消息历史."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory
        from models.session.schemas import Message, MessageType

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        session_mem.add_message(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量是存储数据的容器",
                receiver="all",
            )
        )

        mock_summary_fn = lambda p: "摘要"
        manager = MemoryManager(session_memory=session_mem, summary_fn=mock_summary_fn)

        manager.summarize_checkpoint()

        assert session_mem.message_history == []

    def test_summarize_checkpoint_resets_last_summary_update(self):
        """测试 summarize_checkpoint 重置 last_summary_update."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory
        from models.session.schemas import Message, MessageType

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        session_mem.add_message(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量",
                receiver="all",
            )
        )
        session_mem.last_summary_update = 1

        mock_summary_fn = lambda p: "摘要"
        manager = MemoryManager(session_memory=session_mem, summary_fn=mock_summary_fn)

        manager.summarize_checkpoint()

        assert session_mem.last_summary_update == 0

    def test_summarize_checkpoint_empty_history_returns_none(self):
        """测试空消息历史时返回 None."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_summary_fn = lambda p: "摘要"
        manager = MemoryManager(session_memory=session_mem, summary_fn=mock_summary_fn)

        result = manager.summarize_checkpoint()

        assert result is None
        assert session_mem.checkpoint_summaries == []

    def test_summarize_checkpoint_no_summary_fn_returns_none(self):
        """测试无 summary_fn 时返回 None，但仍清除消息历史."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory
        from models.session.schemas import Message, MessageType

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        session_mem.add_message(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量",
                receiver="all",
            )
        )

        manager = MemoryManager(session_memory=session_mem, summary_fn=None)

        result = manager.summarize_checkpoint()

        assert result is None
        assert session_mem.checkpoint_summaries == []
        assert session_mem.message_history == []

    def test_summarize_checkpoint_summary_failure_still_clears_history(self):
        """测试摘要生成失败时仍然清除消息历史."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory
        from models.session.schemas import Message, MessageType

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        session_mem.add_message(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量",
                receiver="all",
            )
        )

        def failing_summary_fn(p):
            raise RuntimeError("LLM 调用失败")

        manager = MemoryManager(session_memory=session_mem, summary_fn=failing_summary_fn)

        with pytest.raises(RuntimeError, match="LLM 调用失败"):
            manager.summarize_checkpoint()

        # 即使异常，消息历史已被清除（因为 clear 在 append 之后）
        # 但摘要未被追加
        assert session_mem.checkpoint_summaries == []

    def test_summarize_checkpoint_accumulates_multiple_summaries(self):
        """测试多次调用 summarize_checkpoint 累积摘要."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory
        from models.session.schemas import Message, MessageType

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        call_count = 0

        def mock_fn(p):
            nonlocal call_count
            call_count += 1
            return f"检查点{call_count}摘要"

        manager = MemoryManager(session_memory=session_mem, summary_fn=mock_fn)

        # 第一个检查点
        session_mem.add_message(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量",
                receiver="all",
            )
        )
        manager.summarize_checkpoint()

        # 第二个检查点
        session_mem.add_message(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="列表",
                receiver="all",
            )
        )
        manager.summarize_checkpoint()

        assert session_mem.checkpoint_summaries == [
            "检查点1摘要",
            "检查点2摘要",
        ]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestMemoryManagerSummarizeCheckpoint -v`
Expected: FAIL — `AttributeError: 'MemoryManager' object has no attribute 'summarize_checkpoint'`

- [ ] **Step 3: 实现代码（try/finally 保证清除）**

在 `backend/agents/memories/memory_manager.py` 的 `MemoryManager` 类中，在 `_check_and_update_summary()` 方法之后新增：

```python
    def summarize_checkpoint(self) -> str | None:
        """生成当前检查点的摘要并重置消息历史.

        使用 try/finally 确保 message_history 无论摘要成功与否都会被清除。
        摘要失败时只丢失叙事上下文，TeacherAgentMemory 的结构化状态不受影响。

        Returns:
            生成的检查点摘要，如果无法生成则返回 None
        """
        messages = self.session_memory.message_history
        if not messages:
            return None

        if self.summary_fn is None:
            self.session_memory.clear_message_history()
            return None

        summary = None
        try:
            prompt = (
                "请将以下课堂对话摘要为一段简洁的教学总结（100字以内）。\n"
                "重点包括：讲授了什么知识点、学生理解情况、发现的误解。\n\n"
                + "\n".join(
                    f"[{m.sender}]: {m.content}" for m in messages
                )
            )
            summary = self.summary_fn(prompt)
            if summary:
                self.session_memory.checkpoint_summaries.append(summary)
        finally:
            # 无论摘要是否成功生成，都清除消息历史
            self.session_memory.clear_message_history()

        return summary
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && pytest tests/units/test_memory_manager.py::TestMemoryManagerSummarizeCheckpoint -v`
Expected: PASS（包括异常场景 test_summarize_checkpoint_summary_failure_still_clears_history）

- [ ] **Step 5: 运行全部 MemoryManager 测试确保无回归**

Run: `cd backend && pytest tests/units/test_memory_manager.py -v`
Expected: 全部 PASS

- [ ] **Step 6: 提交**

```bash
cd backend && git add agents/memories/memory_manager.py tests/units/test_memory_manager.py
git commit -m "feat(memory-manager): 新增 summarize_checkpoint() 方法"
```

---

### Task 5: TeacherAgent.end_feedback() 使用轻量级上下文

**Files:**
- Modify: `backend/agents/teacher_agent.py`
- Test: `backend/tests/unit_llm/test_teacher_agent.py`

- [ ] **Step 1: 写失败测试 — end_feedback 使用 get_full_context**

在 `backend/tests/unit_llm/test_teacher_agent.py` 中新增测试类：

```python
class TestEndFeedbackWithContextIsolation:
    """测试 end_feedback 使用检查点摘要上下文."""

    def test_end_feedback_uses_full_context_not_agent_context(self):
        """测试 end_feedback 使用 get_full_context 而非 get_agent_context."""
        from unittest.mock import MagicMock, patch

        agent = self._make_agent()
        agent.session_memory.checkpoint_summaries = [
            "检查点1：讲授了变量和类型",
            "检查点2：讲授了列表和字典",
        ]

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "课程总结：变量、列表、字典"

        # 替换 agent 的 llm
        agent.llm = mock_llm

        agent.end_feedback()

        # 验证 system prompt 包含检查点摘要
        call_args = mock_llm.invoke.call_args[0][0]
        system_prompt = call_args[0]["content"]

        assert "检查点1：讲授了变量和类型" in system_prompt
        assert "检查点2：讲授了列表和字典" in system_prompt

    def test_end_feedback_uses_lightweight_context(self):
        """测试 end_feedback 不包含大量历史消息."""
        from unittest.mock import MagicMock

        agent = self._make_agent()
        # 添加大量历史消息（模拟一整堂课）
        from models.session.schemas import Message, MessageType
        for i in range(50):
            agent.session_memory.add_message(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"讲授内容{i}",
                    receiver="all",
                )
            )

        # 添加检查点摘要
        agent.session_memory.checkpoint_summaries = ["检查点1摘要"]

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "课程总结"
        agent.llm = mock_llm

        agent.end_feedback()

        call_args = mock_llm.invoke.call_args[0][0]
        system_prompt = call_args[0]["content"]

        # 验证不包含 "讲授内容0" 等原始消息
        assert "讲授内容0" not in system_prompt
        # 验证包含检查点摘要
        assert "检查点1摘要" in system_prompt

    def test_build_end_feedback_context(self):
        """测试 _build_end_feedback_context 方法存在且返回字符串."""
        agent = self._make_agent()

        context = agent._build_end_feedback_context()

        assert isinstance(context, str)
        assert "Python基础" in context  # topic

    def test_end_feedback_records_message_to_history(self):
        """回归测试：end_feedback 调用后 message_history 包含 END_FEEDBACK 消息.

        验证切换到 get_full_context() 后，_record_message 仍然正常工作。
        """
        from unittest.mock import MagicMock

        agent = self._make_agent()

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "课程总结完毕"
        agent.llm = mock_llm

        agent.end_feedback()

        # 验证 END_FEEDBACK 消息被记录到 message_history
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.END_FEEDBACK
        assert agent.session_memory.message_history[0].content == "课程总结完毕"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/unit_llm/test_teacher_agent.py::TestEndFeedbackWithContextIsolation -v`
Expected: FAIL — `AttributeError: 'TeacherAgent' object has no attribute '_build_end_feedback_context'`

- [ ] **Step 3: 实现最小代码**

在 `backend/agents/teacher_agent.py` 中：

1. 在 `end_feedback()` 方法之前新增 `_build_end_feedback_context()` 方法：

```python
    def _build_end_feedback_context(self) -> str:
        """构建最终总结的轻量级上下文.

        使用累积的检查点摘要 + 教师记忆，而非原始消息历史。
        注意：此方法故意不包含教学模式指令（_MODE_INSTRUCTIONS），
        因为最终总结不需要区分灌输式/启发式/讨论式。
        """
        topic = self.session_memory.topic
        teacher_context = self.memory_manager.teacher_memory.get_system_prompt_addition(topic=topic)
        full_context = self.session_memory.get_full_context()

        return f"""你是教师，正在对本次课程进行最终总结。

## 基本信息
- 教学主题: {topic}

{teacher_context}

{full_context}
"""
```

2. 修改 `end_feedback()` 方法，将 `self._build_system_prompt()` 替换为 `self._build_end_feedback_context()`：

```python
    def end_feedback(self) -> str:
        """生成课程结束总结和反馈.

        Returns:
            课程总结反馈内容

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_end_feedback_context()  # 修改这一行

        user_prompt = (
            f"课程即将结束，请对本次教学进行总结。\n\n"
            f"教学主题: {self.session_memory.topic}\n"
            f"请包含:\n"
            f"1. 本次课程的核心知识点回顾\n"
            f"2. 对学生学习情况的评价\n"
            f"3. 课后学习建议"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "课程总结",
            messages,
            temperature=DEFAULT_TEACHING_TEMPERATURE,
        )

        if not content or not content.strip():
            raise RuntimeError("教师课程总结 LLM 返回空内容")

        self._record_message(content, MessageType.END_FEEDBACK)
        return content
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && pytest tests/unit_llm/test_teacher_agent.py::TestEndFeedbackWithContextIsolation -v`
Expected: PASS

- [ ] **Step 5: 运行全部 TeacherAgent 测试确保无回归**

Run: `cd backend && pytest tests/unit_llm/test_teacher_agent.py -v`
Expected: 全部 PASS

- [ ] **Step 6: 提交**

```bash
cd backend && git add agents/teacher_agent.py tests/unit_llm/test_teacher_agent.py
git commit -m "feat(teacher-agent): end_feedback 使用轻量级检查点摘要上下文"
```

---

### Task 6: SessionOrchestrator 在检查点完成后调用摘要

**Files:**
- Modify: `backend/models/session/services/observation_service.py`
- Test: `backend/tests/unit_llm/test_session_orchestrator.py`

- [ ] **Step 1: 写失败测试 — 检查点完成后消息历史被清除**

在 `backend/tests/unit_llm/test_session_orchestrator.py` 中新增测试类：

```python
class TestCheckpointContextIsolation:
    """测试检查点完成后上下文隔离."""

    @pytest.mark.asyncio
    async def test_teach_checkpoint_clears_message_history(self):
        """测试 _teach_checkpoint 完成后清除消息历史."""
        from unittest.mock import AsyncMock, MagicMock

        # 创建 session_memory 并添加消息
        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        student_mem = StudentAgentMemory.from_profile(
            StudentProfile(name="Alice", level=StudentLevel.EXCELLENT, learning_ability=8)
        )

        # 创建 mock teacher agent
        mock_teacher = MagicMock()
        mock_teacher.deliver_lecture.return_value = "变量是存储数据的容器"

        # 创建 mock student agent
        mock_student = MagicMock()
        mock_student.profile.name = "Alice"
        mock_student.should_respond.return_value = False

        plan = CheckpointPlan(
            topic="Python基础",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(
                    title="变量",
                    key_point="变量是存储数据的容器",
                )
            ],
        )

        manager = MemoryManager(
            session_memory=session_mem,
            teacher_memory=teacher_mem,
            student_memories={"Alice": student_mem},
            summary_fn=lambda p: "检查点1摘要",
        )

        from models.session.services.observation_service import SessionOrchestrator

        orchestrator = SessionOrchestrator(
            teacher_agent=mock_teacher,
            student_agents=[mock_student],
            checkpoint_plan=plan,
            memory_manager=manager,
            message_service=AsyncMock(),
        )

        await orchestrator._teach_checkpoint(plan.checkpoints[0])

        # 验证消息历史被清除
        assert session_mem.message_history == []
        # 验证摘要被保存
        assert session_mem.checkpoint_summaries == ["检查点1摘要"]

    @pytest.mark.asyncio
    async def test_multiple_checkpoints_accumulate_summaries(self):
        """测试多个检查点累积摘要."""
        from unittest.mock import AsyncMock, MagicMock

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()

        mock_teacher = MagicMock()
        mock_teacher.deliver_lecture.return_value = "讲授内容"

        mock_student = MagicMock()
        mock_student.profile.name = "Alice"
        mock_student.should_respond.return_value = False

        plan = CheckpointPlan(
            topic="Python基础",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(title="变量", key_point="变量"),
                Checkpoint(title="列表", key_point="列表"),
            ],
        )

        call_count = 0

        def mock_summary(p):
            nonlocal call_count
            call_count += 1
            return f"摘要{call_count}"

        manager = MemoryManager(
            session_memory=session_mem,
            teacher_memory=teacher_mem,
            summary_fn=mock_summary,
        )

        from models.session.services.observation_service import SessionOrchestrator

        orchestrator = SessionOrchestrator(
            teacher_agent=mock_teacher,
            student_agents=[mock_student],
            checkpoint_plan=plan,
            memory_manager=manager,
            message_service=AsyncMock(),
        )

        await orchestrator._teach_checkpoint(plan.checkpoints[0])
        await orchestrator._teach_checkpoint(plan.checkpoints[1])

        assert session_mem.checkpoint_summaries == ["摘要1", "摘要2"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/unit_llm/test_session_orchestrator.py::TestCheckpointContextIsolation -v`
Expected: FAIL — `assert session_mem.message_history == []` 失败（消息历史未被清除）

- [ ] **Step 3: 实现最小代码**

在 `backend/models/session/services/observation_service.py` 的 `_teach_checkpoint()` 方法中，在 `await self._ws_push_checkpoint_state(checkpoint)` 之后、`await self._trigger_observer_learning_for_checkpoint(checkpoint)` 之前，新增一行：

```python
        # 检查点完成后生成摘要并重置上下文
        # 在 observer learning 之前调用，因为 observer learning 不依赖 message_history
        self.memory_manager.summarize_checkpoint()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && pytest tests/unit_llm/test_session_orchestrator.py::TestCheckpointContextIsolation -v`
Expected: PASS

- [ ] **Step 5: 运行全部 SessionOrchestrator 测试确保无回归**

Run: `cd backend && pytest tests/unit_llm/test_session_orchestrator.py -v`
Expected: 全部 PASS

- [ ] **Step 6: 提交**

```bash
cd backend && git add models/session/services/observation_service.py tests/unit_llm/test_session_orchestrator.py
git commit -m "feat(observation): 检查点完成后生成摘要并重置上下文"
```

---

### Task 7: TeacherSessionController 在检查点推进时调用摘要

**Files:**
- Modify: `backend/models/session/services/teacher_service.py`
- Test: `backend/tests/units/test_teacher_controller.py`

- [ ] **Step 1: 写失败测试 — advance_checkpoint 触发摘要**

在 `backend/tests/units/test_teacher_controller.py` 中新增测试类。使用 `unittest.mock.patch` mock `summarize_checkpoint`：

```python
class TestCheckpointContextIsolation:
    """测试教师模式检查点上下文隔离."""

    def test_advance_checkpoint_calls_summarize(self):
        """测试推进检查点时调用 summarize_checkpoint."""
        from unittest.mock import MagicMock, patch

        # 创建最小化的 controller（参考现有 test 的创建模式）
        from agents.memories.memory_manager import MemoryManager, SessionMemory
        from agents.memories.teacher_memory import TeacherAgentMemory
        from models.checkpoint.schemas import Checkpoint, CheckpointPlan
        from models.session.services.teacher_service import TeacherSessionController

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)

        plan = CheckpointPlan(
            topic="Python基础",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(title="变量", key_point="变量"),
                Checkpoint(title="列表", key_point="列表"),
            ],
        )

        # mock 所有外部依赖
        with patch("models.session.services.teacher_service.get_connection_manager"):
            controller = TeacherSessionController(
                session_id=1,
                topic="Python基础",
                teaching_mode="didactic",
                checkpoint_plan=plan,
                memory_manager=mm,
                students=[],
                llm=MagicMock(),
            )

        # mock summarize_checkpoint
        controller.memory_manager.summarize_checkpoint = MagicMock()

        controller.handle_advance_checkpoint()

        controller.memory_manager.summarize_checkpoint.assert_called_once()
```

注意：此测试依赖 `TeacherSessionController` 的构造函数签名。如果构造函数需要额外参数或初始化方式不同，需根据 `teacher_service.py` 的实际代码调整。

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/units/test_teacher_controller.py::TestCheckpointContextIsolation -v`
Expected: FAIL — `summarize_checkpoint` 未被调用

- [ ] **Step 3: 实现最小代码**

在 `backend/models/session/services/teacher_service.py` 的 `handle_advance_checkpoint()` 方法中，在 `handle_end_dialogue()` 调用之后、方法末尾新增：

```python
        # 检查点推进后生成摘要并重置上下文
        self.memory_manager.summarize_checkpoint()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && pytest tests/units/test_teacher_controller.py::TestCheckpointContextIsolation -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd backend && git add models/session/services/teacher_service.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): 检查点推进时生成摘要并重置上下文"
```

---

### Task 8: ORM 模型和持久化更新

**Files:**
- Modify: `backend/orm/session_memory.py`
- Modify: `backend/agents/memories/memory_persistence.py`
- Test: `backend/tests/integration/test_memory_persistence.py`（或现有持久化测试文件）

- [ ] **Step 1: 写失败测试 — checkpoint_summaries 持久化和恢复**

在现有的持久化测试文件中新增（或创建新测试文件）：

```python
    @pytest.mark.asyncio
    async def test_save_and_load_checkpoint_summaries(self, db_session):
        """测试 checkpoint_summaries 的保存和加载."""
        from agents.memories.memory_manager import SessionMemory
        from agents.memories.memory_persistence import MemoryPersistence

        persistence = MemoryPersistence(db_session)

        # 创建带 checkpoint_summaries 的 SessionMemory
        memory = SessionMemory(
            session_id=1,
            topic="Python基础",
            checkpoint_summaries=["检查点1摘要", "检查点2摘要"],
        )

        # 保存
        await persistence.save_session_memory(memory)

        # 加载
        loaded = await persistence.load_session_memory(1)

        assert loaded is not None
        assert loaded.checkpoint_summaries == ["检查点1摘要", "检查点2摘要"]
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && pytest tests/integration/test_memory_persistence.py -v -k "checkpoint_summaries"`
Expected: FAIL — `checkpoint_summaries` 未被持久化

- [ ] **Step 3: 实现最小代码**

1. 在 `backend/orm/session_memory.py` 的 `SessionMemoryModel` 中新增列：

```python
    checkpoint_summaries: Mapped[list | None] = mapped_column(JSON, nullable=True)
```

2. 在 `backend/agents/memories/memory_persistence.py` 的 `save_session_memory()` 中，在 `update_fn` 中新增：

```python
        existing.checkpoint_summaries = memory.checkpoint_summaries
```

在 `create_fn` 中新增：

```python
            "checkpoint_summaries": memory.checkpoint_summaries,
```

3. 在 `load_session_memory()` 中，在构造 `SessionMemory` 时新增：

```python
        checkpoint_summaries=record.checkpoint_summaries or [],
```

- [ ] **Step 4: 生成 Alembic 迁移**

Run: `cd backend && alembic revision --autogenerate -m "add checkpoint_summaries to session_memories"`

- [ ] **Step 5: 运行测试验证通过**

Run: `cd backend && pytest tests/integration/test_memory_persistence.py -v -k "checkpoint_summaries"`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd backend && git add orm/session_memory.py agents/memories/memory_persistence.py tests/ alembic/versions/
git commit -m "feat(persistence): checkpoint_summaries 持久化支持"
```

---

### Task 9: 运行全部测试并验证无回归

**Files:** 无新改动

- [ ] **Step 1: 运行全部单元测试**

Run: `cd backend && pytest tests/units/ -v`
Expected: 全部 PASS（包括新增的 SessionMemory 和 MemoryManager 测试）

- [ ] **Step 2: 运行全部 unit_llm 测试**

Run: `cd backend && pytest tests/unit_llm/ -v`
Expected: 全部 PASS（包括新增的 TeacherAgent 和 SessionOrchestrator 测试）

- [ ] **Step 3: Ruff 代码检查**

Run: `cd backend && ruff check agents/memories/ agents/teacher_agent.py models/session/services/`
Expected: 无错误

- [ ] **Step 4: Ruff 格式化**

Run: `cd backend && ruff format agents/memories/ agents/teacher_agent.py models/session/services/`
Expected: 无格式问题

- [ ] **Step 5: 最终提交（如有修复）**

```bash
cd backend && git add -A && git commit -m "fix: 测试和 lint 修复"
```

---

### Task 10: 更新文档

**Files:**
- Modify: `docs/api.md`（如有 API 变更 — 本次无 API 变更，跳过）
- Modify: `docs/tests/backend/index.md`

- [ ] **Step 1: 更新测试文档**

在 `docs/tests/backend/index.md` 中新增测试类描述：

```markdown
### tests/units/test_memory_manager.py
MemoryManager 和 SessionMemory 单元测试

- **TestSessionMemory** — SessionMemory 测试类
  - `test_init_checkpoint_summaries_default()` — 测试 checkpoint_summaries 默认为空列表
- **TestSessionMemoryClearHistory** — clear_message_history() 测试类
  - `test_clear_message_history_empties_list()` — 测试清空消息列表
  - `test_clear_message_history_resets_last_summary_update()` — 测试重置摘要更新计数器
  - `test_clear_message_history_preserves_checkpoint_summaries()` — 测试不影响检查点摘要
- **TestSessionMemoryGetFullContext** — get_full_context() 测试类
  - `test_get_full_context_includes_topic()` — 测试包含教学主题
  - `test_get_full_context_includes_checkpoint_summaries()` — 测试包含检查点摘要
  - `test_get_full_context_includes_teaching_summary()` — 测试包含教学摘要
  - `test_get_full_context_includes_recent_messages()` — 测试包含最近消息
  - `test_get_full_context_empty_state()` — 测试空状态
- **TestMemoryManagerSummarizeCheckpoint** — summarize_checkpoint() 测试类
  - `test_summarize_checkpoint_appends_summary()` — 测试摘要追加
  - `test_summarize_checkpoint_clears_message_history()` — 测试清空消息历史
  - `test_summarize_checkpoint_resets_last_summary_update()` — 测试重置计数器
  - `test_summarize_checkpoint_empty_history_returns_none()` — 测试空历史返回 None
  - `test_summarize_checkpoint_no_summary_fn_returns_none()` — 测试无摘要函数返回 None
  - `test_summarize_checkpoint_summary_failure_still_clears_history()` — 测试摘要失败仍清除历史
  - `test_summarize_checkpoint_accumulates_multiple_summaries()` — 测试多次调用累积摘要

### tests/unit_llm/test_teacher_agent.py
TeacherAgent 单元测试（使用 mock LLM）

- **TestEndFeedbackWithContextIsolation** — end_feedback 上下文隔离测试类
  - `test_end_feedback_uses_full_context_not_agent_context()` — 测试使用检查点摘要上下文
  - `test_end_feedback_uses_lightweight_context()` — 测试不包含大量历史消息
  - `test_build_end_feedback_context()` — 测试方法存在且返回正确格式

### tests/unit_llm/test_session_orchestrator.py
SessionOrchestrator 单元测试（使用 mock LLM）

- **TestCheckpointContextIsolation** — 检查点上下文隔离测试类
  - `test_teach_checkpoint_clears_message_history()` — 测试检查点完成后清除消息历史
  - `test_multiple_checkpoints_accumulate_summaries()` — 测试多检查点累积摘要
```

- [ ] **Step 2: 提交**

```bash
git add docs/tests/backend/index.md
git commit -m "docs(tests): 新增上下文隔离测试文档"
```

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 3 | CLEAR | 2 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**VERDICT:** ENG CLEARED — ready to implement
