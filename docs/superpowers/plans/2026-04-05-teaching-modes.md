# 三种教学模式实现 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 TeacherAgent 添加提问、回复、作业、评分、反馈等方法，使三种教学模式（灌输式/启发式/讨论式）拥有完整的交互能力。

**Architecture:** 在现有 TeacherAgent 基础上添加 5 个新方法。每个方法复用 `_build_system_prompt()` 构建 system prompt，通过不同的 user prompt 实现差异化行为。所有消息通过 MemoryManager 记录。MemoryManager 新增对 ASSIGN_HOMEWORK、HOMEWORK_SUBMISSION、HOMEWORK_FEEDBACK、END_FEEDBACK、FEEDBACK_SUBMISSION 消息类型的处理。编排逻辑（何时调用哪个方法）属于 Phase 7 SessionOrchestrator。

**Tech Stack:** Python 3.12+, LangChain (LLMClient mock), Pydantic, pytest, unittest.mock

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/agents/teacher_agent.py` | 修改 | 新增 5 个交互方法 + `_record_message` 通用方法 |
| `backend/tests/units/test_teacher_agent.py` | 修改 | 新增 ~28 个单元测试（6 个测试类） |
| `backend/agents/memories/memory_manager.py` | 修改 | `process_message` 新增 5 种消息类型处理 |
| `backend/tests/units/test_memory_manager.py` | 修改 | 新增 5 个测试 |

## 已有代码依赖

- `backend/agents/teacher_agent.py` — TeacherAgent（deliver_lecture, _build_system_prompt, _get_mode_temperature, _record_lecture）
- `backend/agents/memories/memory_manager.py` — MemoryManager（process_message, 目前处理 LECTURE/CHECKPOINT_QUESTION/REPLY_TO_TEACHER/QUESTION_TO_TEACHER/ANSWER_TO_CHECKPOINT）
- `backend/schemas/message.py` — MessageType 枚举（11 种消息类型，其中 5 种未被 MemoryManager 处理）
- `backend/core/llm_utils.py` — `safe_llm_call(fn, caller, description, /, *args, **kwargs) -> T`
- `backend/core/settings.py` — `TEACHING_TEMPERATURES`, `DEFAULT_TEACHING_TEMPERATURE`, `CONTENT_JUDGE_TEMPERATURE`, `TIMEZONE`

## 设计决策

1. **不引入 SessionOrchestrator**: 编排逻辑属于 Phase 7，Phase 6 只提供方法层面的能力。
2. **复用 `_build_system_prompt()`**: 所有新方法共用同一个 system prompt（含模式指令和上下文），通过 user prompt 区分行为。
3. **checkpoint 和 discussion 使用同一 MessageType**: 两者都记录为 `CHECKPOINT_QUESTION`，区别在于 prompt 内容和调用频率（频率由 Phase 7 编排器控制）。
4. **`_record_message` 通用方法**: 将 `_record_lecture` 内联代码提取为通用 `_record_message`，避免每个新方法重复消息创建代码。
5. **`grade_homework` 使用低温度**: 评分需要确定性，使用 `CONTENT_JUDGE_TEMPERATURE` (0.1)。
6. **MemoryManager 新增处理**: 对 ASSIGN_HOMEWORK 等新类型不做特殊业务逻辑，仅确保 process_message 不崩溃（这些消息类型已自动添加到 message_history）。

---

### Task 1: 重构 `_record_message` + 实现 `ask_checkpoint_question()`

**Files:**
- Modify: `backend/agents/teacher_agent.py:129-137`（_record_lecture → _record_message）
- Modify: `backend/tests/units/test_teacher_agent.py`

- [ ] **Step 1: Write the failing tests for `ask_checkpoint_question`**

在 `backend/tests/units/test_teacher_agent.py` 末尾添加：

```python
class TestTeacherAgentCheckpointQuestion:
    """TeacherAgent ask_checkpoint_question 测试."""

    def _make_agent(self, teaching_mode: str = "heuristic", covered_topics: list[str] | None = None):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "请问变量的作用域有哪些？"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_ask_checkpoint_question_calls_llm(self):
        """测试 ask_checkpoint_question 调用 LLM."""
        agent = self._make_agent()
        agent.ask_checkpoint_question()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_ask_checkpoint_question_prompt_includes_covered_topics(self):
        """测试 prompt 包含已讲授知识点."""
        agent = self._make_agent(covered_topics=["变量", "数据类型"])
        agent.ask_checkpoint_question()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "变量" in user_msg

    def test_ask_checkpoint_question_uses_mode_temperature(self):
        """测试使用对应模式的温度."""
        agent = self._make_agent(teaching_mode="heuristic")
        agent.ask_checkpoint_question()
        assert agent.llm.invoke.call_args[1].get("temperature") == 0.5

    def test_ask_checkpoint_question_returns_content(self):
        """测试返回 LLM 生成的问题内容."""
        agent = self._make_agent()
        result = agent.ask_checkpoint_question()
        assert result == "请问变量的作用域有哪些？"

    def test_ask_checkpoint_question_records_message(self):
        """测试记录为 CHECKPOINT_QUESTION 消息."""
        agent = self._make_agent()
        agent.ask_checkpoint_question()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.CHECKPOINT_QUESTION
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentCheckpointQuestion -v`
Expected: FAIL — `AttributeError: 'TeacherAgent' object has no attribute 'ask_checkpoint_question'`

- [ ] **Step 3: Refactor `_record_lecture` to `_record_message` and implement `ask_checkpoint_question`**

在 `backend/agents/teacher_agent.py` 中：

1. 将 `_record_lecture` 方法改为通用 `_record_message`：

```python
    def _record_message(self, content: str, message_type: MessageType) -> None:
        """通过 MemoryManager 记录消息."""
        message = Message(
            sender="teacher",
            message_type=message_type,
            content=content,
            timestamp=datetime.now(TIMEZONE),
        )
        self.memory_manager.process_message(message)
```

2. 更新 `_record_lecture` 调用新方法（保持向后兼容）：

```python
    def _record_lecture(self, content: str) -> None:
        """通过 MemoryManager 记录讲授消息."""
        self._record_message(content, MessageType.LECTURE)
```

3. 在 `deliver_lecture` 方法之后、`deliver_lecture_stream` 方法之前，添加 `ask_checkpoint_question`：

```python
    def ask_checkpoint_question(self) -> str:
        """提出 checkpoint 问题（启发式模式）.

        基于已讲授的知识点生成一个检查理解程度的问题。

        Returns:
            问题文本

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()
        covered = self.memory_manager.teacher_memory.covered_topics
        recent_topics = covered[-5:] if covered else []
        topics_str = "、".join(recent_topics) if recent_topics else self.session_memory.topic

        user_prompt = (
            f"基于刚才讲授的内容，请提出一个 checkpoint 问题来检查学生的理解程度。\n"
            f"最近讲授的知识点: {topics_str}\n"
            f"要求: 问题应该紧扣已讲授内容，难度适中。只输出问题本身。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "checkpoint 提问",
            messages,
            temperature=self._get_mode_temperature(),
        )

        if not content or not content.strip():
            raise RuntimeError("教师 checkpoint 提问 LLM 返回空内容")

        self._record_message(content, MessageType.CHECKPOINT_QUESTION)
        return content
```

- [ ] **Step 4: Run new tests to verify they pass**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentCheckpointQuestion -v`
Expected: 5 passed

- [ ] **Step 5: Run existing TeacherAgent tests to verify no regression**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py -v`
Expected: All 29 tests pass (24 existing + 5 new)

- [ ] **Step 6: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat(teacher-agent): add ask_checkpoint_question + refactor _record_message"
```

---

### Task 2: 实现 `ask_discussion_question()`

**Files:**
- Modify: `backend/agents/teacher_agent.py`
- Modify: `backend/tests/units/test_teacher_agent.py`

- [ ] **Step 1: Write the failing tests**

在 `backend/tests/units/test_teacher_agent.py` 末尾添加：

```python
class TestTeacherAgentDiscussionQuestion:
    """TeacherAgent ask_discussion_question 测试."""

    def _make_agent(self, teaching_mode: str = "discussion", covered_topics: list[str] | None = None):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "大家觉得在实际项目中，什么时候应该用列表，什么时候应该用元组？"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_ask_discussion_question_calls_llm(self):
        """测试 ask_discussion_question 调用 LLM."""
        agent = self._make_agent()
        agent.ask_discussion_question()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_ask_discussion_question_prompt_includes_topic(self):
        """测试 prompt 包含教学主题."""
        agent = self._make_agent()
        agent.ask_discussion_question()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "Python基础" in user_msg

    def test_ask_discussion_question_uses_mode_temperature(self):
        """测试讨论式模式使用 0.7 温度."""
        agent = self._make_agent(teaching_mode="discussion")
        agent.ask_discussion_question()
        assert agent.llm.invoke.call_args[1].get("temperature") == 0.7

    def test_ask_discussion_question_returns_content(self):
        """测试返回 LLM 生成的讨论问题."""
        agent = self._make_agent()
        result = agent.ask_discussion_question()
        assert result == "大家觉得在实际项目中，什么时候应该用列表，什么时候应该用元组？"

    def test_ask_discussion_question_records_as_checkpoint(self):
        """测试记录为 CHECKPOINT_QUESTION 消息."""
        agent = self._make_agent()
        agent.ask_discussion_question()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.CHECKPOINT_QUESTION
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentDiscussionQuestion -v`
Expected: FAIL — `AttributeError: 'TeacherAgent' object has no attribute 'ask_discussion_question'`

- [ ] **Step 3: Implement `ask_discussion_question`**

在 `backend/agents/teacher_agent.py` 的 `ask_checkpoint_question` 方法之后添加：

```python
    def ask_discussion_question(self) -> str:
        """提出讨论问题（讨论式模式）.

        基于当前教学内容引导开放性讨论。

        Returns:
            问题文本

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            f"请基于当前教学内容「{self.session_memory.topic}」提出一个开放性的讨论问题。\n"
            f"要求:\n"
            f"- 问题应该能引发学生思考和讨论\n"
            f"- 鼓励学生表达自己的观点\n"
            f"- 可以结合实际案例或应用场景\n"
            f"只输出问题本身。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "讨论提问",
            messages,
            temperature=self._get_mode_temperature(),
        )

        if not content or not content.strip():
            raise RuntimeError("教师讨论提问 LLM 返回空内容")

        self._record_message(content, MessageType.CHECKPOINT_QUESTION)
        return content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentDiscussionQuestion -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat(teacher-agent): add ask_discussion_question method"
```

---

### Task 3: 实现 `reply_to_student()`

**Files:**
- Modify: `backend/agents/teacher_agent.py`
- Modify: `backend/tests/units/test_teacher_agent.py`

- [ ] **Step 1: Write the failing tests**

在 `backend/tests/units/test_teacher_agent.py` 末尾添加：

```python
class TestTeacherAgentReplyToStudent:
    """TeacherAgent reply_to_student 测试."""

    def _make_agent(self, teaching_mode: str = "heuristic"):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "回答得很好！变量确实有局部和全局两种作用域。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_reply_to_student_calls_llm(self):
        """测试 reply_to_student 调用 LLM."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_reply_to_student_prompt_includes_student_name(self):
        """测试 prompt 包含学生名字."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "张三" in user_msg

    def test_reply_to_student_prompt_includes_student_message(self):
        """测试 prompt 包含学生消息内容."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "变量有局部和全局作用域" in user_msg

    def test_reply_to_student_returns_content(self):
        """测试返回 LLM 生成的回复内容."""
        agent = self._make_agent()
        result = agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        assert result == "回答得很好！变量确实有局部和全局两种作用域。"

    def test_reply_to_student_records_as_teacher_reply(self):
        """测试记录为 TEACHER_REPLY 消息."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.TEACHER_REPLY
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentReplyToStudent -v`
Expected: FAIL — `AttributeError: 'TeacherAgent' object has no attribute 'reply_to_student'`

- [ ] **Step 3: Implement `reply_to_student`**

在 `backend/agents/teacher_agent.py` 的 `ask_discussion_question` 方法之后添加：

```python
    def reply_to_student(self, student_name: str, student_message: str) -> str:
        """回复学生的回答或提问.

        Args:
            student_name: 学生名字
            student_message: 学生的回答或提问内容

        Returns:
            教师的回复内容

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            f"学生「{student_name}」说：{student_message}\n\n"
            f"请对这位学生的回答/提问给予反馈。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "回复学生",
            messages,
            temperature=self._get_mode_temperature(),
        )

        if not content or not content.strip():
            raise RuntimeError("教师回复学生 LLM 返回空内容")

        self._record_message(content, MessageType.TEACHER_REPLY)
        return content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentReplyToStudent -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat(teacher-agent): add reply_to_student method"
```

---

### Task 4: 实现 `assign_homework()`

**Files:**
- Modify: `backend/agents/teacher_agent.py`
- Modify: `backend/tests/units/test_teacher_agent.py`

- [ ] **Step 1: Write the failing tests**

在 `backend/tests/units/test_teacher_agent.py` 末尾添加：

```python
class TestTeacherAgentAssignHomework:
    """TeacherAgent assign_homework 测试."""

    def _make_agent(self, covered_topics: list[str] | None = None):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "作业：请编写一个函数，实现列表的排序功能。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_assign_homework_calls_llm(self):
        """测试 assign_homework 调用 LLM."""
        agent = self._make_agent()
        agent.assign_homework()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_assign_homework_prompt_includes_topic_and_topics(self):
        """测试 prompt 包含教学主题和已讲授知识点."""
        agent = self._make_agent(covered_topics=["变量", "函数"])
        agent.assign_homework()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "Python基础" in user_msg
        assert "变量" in user_msg

    def test_assign_homework_returns_content(self):
        """测试返回作业内容."""
        agent = self._make_agent()
        result = agent.assign_homework()
        assert result == "作业：请编写一个函数，实现列表的排序功能。"

    def test_assign_homework_records_as_assign_homework(self):
        """测试记录为 ASSIGN_HOMEWORK 消息."""
        agent = self._make_agent()
        agent.assign_homework()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.ASSIGN_HOMEWORK
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentAssignHomework -v`
Expected: FAIL — `AttributeError: 'TeacherAgent' object has no attribute 'assign_homework'`

- [ ] **Step 3: Implement `assign_homework`**

在 `backend/agents/teacher_agent.py` 的 `reply_to_student` 方法之后添加：

```python
    def assign_homework(self) -> str:
        """布置课后作业.

        基于已讲授的内容生成作业题目。

        Returns:
            作业内容文本

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()
        covered = self.memory_manager.teacher_memory.covered_topics
        topics_str = "、".join(covered) if covered else self.session_memory.topic

        user_prompt = (
            f"请基于以下已讲授内容布置一份课后作业。\n"
            f"教学主题: {self.session_memory.topic}\n"
            f"已讲授的知识点: {topics_str}\n\n"
            f"要求:\n"
            f"- 作业应涵盖主要知识点\n"
            f"- 包含基础题和提高题\n"
            f"- 明确答题要求"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "布置作业",
            messages,
            temperature=DEFAULT_TEACHING_TEMPERATURE,
        )

        if not content or not content.strip():
            raise RuntimeError("教师布置作业 LLM 返回空内容")

        self._record_message(content, MessageType.ASSIGN_HOMEWORK)
        return content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentAssignHomework -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat(teacher-agent): add assign_homework method"
```

---

### Task 5: 实现 `grade_homework()`

**Files:**
- Modify: `backend/agents/teacher_agent.py`
- Modify: `backend/tests/units/test_teacher_agent.py`

- [ ] **Step 1: Write the failing tests**

在 `backend/tests/units/test_teacher_agent.py` 末尾添加：

```python
class TestTeacherAgentGradeHomework:
    """TeacherAgent grade_homework 测试."""

    def _make_agent(self):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "评分：良好。优点：函数逻辑正确。改进：缺少边界条件处理。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_grade_homework_calls_llm(self):
        """测试 grade_homework 调用 LLM."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_grade_homework_prompt_includes_student_name(self):
        """测试 prompt 包含学生名字."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "张三" in user_msg

    def test_grade_homework_prompt_includes_homework_content(self):
        """测试 prompt 包含作业内容."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "def sort" in user_msg

    def test_grade_homework_uses_low_temperature(self):
        """测试使用低温度进行评分（CONTENT_JUDGE_TEMPERATURE）."""
        from core.settings import CONTENT_JUDGE_TEMPERATURE

        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        assert agent.llm.invoke.call_args[1].get("temperature") == CONTENT_JUDGE_TEMPERATURE

    def test_grade_homework_records_as_homework_feedback(self):
        """测试记录为 HOMEWORK_FEEDBACK 消息."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.HOMEWORK_FEEDBACK
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentGradeHomework -v`
Expected: FAIL — `AttributeError: 'TeacherAgent' object has no attribute 'grade_homework'`

- [ ] **Step 3: Implement `grade_homework`**

在 `backend/agents/teacher_agent.py` 的 `assign_homework` 方法之后添加：

```python
    def grade_homework(self, student_name: str, homework_content: str) -> str:
        """评价学生的作业.

        使用 LLM 评价学生提交的作业。

        Args:
            student_name: 学生名字
            homework_content: 学生提交的作业内容

        Returns:
            评价内容

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            f"请评价以下学生提交的作业。\n\n"
            f"学生: {student_name}\n"
            f"作业内容:\n{homework_content}\n\n"
            f"请给出:\n"
            f"1. 评分（优秀/良好/及格/不及格）\n"
            f"2. 优点\n"
            f"3. 需要改进的地方"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "作业评分",
            messages,
            temperature=CONTENT_JUDGE_TEMPERATURE,
        )

        if not content or not content.strip():
            raise RuntimeError("教师作业评分 LLM 返回空内容")

        self._record_message(content, MessageType.HOMEWORK_FEEDBACK)
        return content
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentGradeHomework -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat(teacher-agent): add grade_homework method"
```

---

### Task 6: 实现 `end_feedback()`

**Files:**
- Modify: `backend/agents/teacher_agent.py`
- Modify: `backend/tests/units/test_teacher_agent.py`

- [ ] **Step 1: Write the failing tests**

在 `backend/tests/units/test_teacher_agent.py` 末尾添加：

```python
class TestTeacherAgentEndFeedback:
    """TeacherAgent end_feedback 测试."""

    def _make_agent(self):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "本次课程我们学习了Python基础，大家表现不错，课后多练习。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_end_feedback_calls_llm(self):
        """测试 end_feedback 调用 LLM."""
        agent = self._make_agent()
        agent.end_feedback()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_end_feedback_prompt_includes_topic(self):
        """测试 prompt 包含教学主题."""
        agent = self._make_agent()
        agent.end_feedback()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "Python基础" in user_msg

    def test_end_feedback_returns_content(self):
        """测试返回课程总结内容."""
        agent = self._make_agent()
        result = agent.end_feedback()
        assert result == "本次课程我们学习了Python基础，大家表现不错，课后多练习。"

    def test_end_feedback_records_as_end_feedback(self):
        """测试记录为 END_FEEDBACK 消息."""
        agent = self._make_agent()
        agent.end_feedback()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.END_FEEDBACK
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentEndFeedback -v`
Expected: FAIL — `AttributeError: 'TeacherAgent' object has no attribute 'end_feedback'`

- [ ] **Step 3: Implement `end_feedback`**

在 `backend/agents/teacher_agent.py` 的 `grade_homework` 方法之后添加：

```python
    def end_feedback(self) -> str:
        """生成课程结束总结和反馈.

        Returns:
            课程总结反馈内容

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()

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

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentEndFeedback -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat(teacher-agent): add end_feedback method"
```

---

### Task 7: MemoryManager 新增消息类型处理

**Files:**
- Modify: `backend/agents/memories/memory_manager.py:38-52`
- Modify: `backend/tests/units/test_memory_manager.py`

- [ ] **Step 1: Write the failing tests**

在 `backend/tests/units/test_memory_manager.py` 的 `TestMemoryManager` 类末尾添加以下方法：

```python
    def test_process_assign_homework_does_not_crash(self):
        """测试处理布置作业消息不崩溃."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("teacher", MessageType.ASSIGN_HOMEWORK, "作业内容")
        manager.process_message(msg)
        assert len(session_mem.message_history) == 1

    def test_process_homework_submission_does_not_crash(self):
        """测试处理学生提交作业消息不崩溃."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("张三", MessageType.HOMEWORK_SUBMISSION, "我的作业答案")
        manager.process_message(msg)
        assert len(session_mem.message_history) == 1

    def test_process_homework_feedback_does_not_crash(self):
        """测试处理作业反馈消息不崩溃."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("teacher", MessageType.HOMEWORK_FEEDBACK, "评分：良好")
        manager.process_message(msg)
        assert len(session_mem.message_history) == 1

    def test_process_end_feedback_does_not_crash(self):
        """测试处理课程结束反馈消息不崩溃."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("teacher", MessageType.END_FEEDBACK, "课程总结")
        manager.process_message(msg)
        assert len(session_mem.message_history) == 1

    def test_process_feedback_submission_does_not_crash(self):
        """测试处理学生课程反馈消息不崩溃."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("张三", MessageType.FEEDBACK_SUBMISSION, "课程很好")
        manager.process_message(msg)
        assert len(session_mem.message_history) == 1
```

- [ ] **Step 2: Run tests to verify they pass (they should already pass)**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_memory_manager.py -v`
Expected: All 44 tests pass (39 existing + 5 new)

注意：这些测试应该已经通过，因为 `process_message` 中的 `if/elif` 链只处理 5 种已知类型，未知类型会自然落入（不做任何特殊处理但消息已添加到 history）。但添加显式的 elif 分支更清晰，也是良好的防御性编程。

- [ ] **Step 3: Add explicit elif branches in `process_message`**

在 `backend/agents/memories/memory_manager.py` 的 `process_message` 方法中，在 `ANSWER_TO_CHECKPOINT` 分支之后添加显式分支：

```python
    def process_message(self, message: "Message") -> None:
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
        elif message.message_type == MessageType.TEACHER_REPLY:
            pass  # 教师回复，已通过 message_history 记录
        elif message.message_type == MessageType.ASSIGN_HOMEWORK:
            pass  # 布置作业，已通过 message_history 记录
        elif message.message_type == MessageType.HOMEWORK_SUBMISSION:
            pass  # 学生提交作业，已通过 message_history 记录
        elif message.message_type == MessageType.HOMEWORK_FEEDBACK:
            pass  # 作业评分，已通过 message_history 记录
        elif message.message_type == MessageType.END_FEEDBACK:
            pass  # 课程结束反馈，已通过 message_history 记录
        elif message.message_type == MessageType.FEEDBACK_SUBMISSION:
            pass  # 学生课程反馈，已通过 message_history 记录

        self._check_and_update_summary()
```

- [ ] **Step 4: Run all MemoryManager tests to verify no regression**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_memory_manager.py -v`
Expected: All 44 tests pass

- [ ] **Step 5: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/agents/memories/memory_manager.py backend/tests/units/test_memory_manager.py
git commit -m "feat(memory-manager): add explicit handlers for all MessageType values"
```

---

### Task 8: 全量验证

**Files:** None (verification only)

- [ ] **Step 1: Run all backend unit tests**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/ -v`
Expected: All 199 tests pass (160 existing + 39 new)

- [ ] **Step 2: Run ruff lint**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && ruff check .`
Expected: No errors

- [ ] **Step 3: Run ruff format check**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && ruff format --check .`
Expected: No formatting issues

- [ ] **Step 4: Verify TeacherAgent public API surface**

确认 `TeacherAgent` 现有以下公开方法：

| 方法 | 用途 | Phase |
|------|------|-------|
| `deliver_lecture()` | 生成讲授内容 | 5 |
| `deliver_lecture_stream()` | 流式讲授 | 5 |
| `is_content_complete()` | 判断内容是否完成 | 5 |
| `ask_checkpoint_question()` | 启发式 checkpoint 提问 | 6 |
| `ask_discussion_question()` | 讨论式讨论提问 | 6 |
| `reply_to_student(name, msg)` | 回复学生 | 6 |
| `assign_homework()` | 布置作业 | 6 |
| `grade_homework(name, content)` | 评分作业 | 6 |
| `end_feedback()` | 课程总结 | 6 |

---

### Task 9: 错误路径测试（空内容）

**Files:**
- Modify: `backend/tests/units/test_teacher_agent.py`

- [ ] **Step 1: Write error path tests for all 5 new methods**

在 `backend/tests/units/test_teacher_agent.py` 末尾添加：

```python
class TestTeacherAgentNewMethodsErrors:
    """TeacherAgent 新方法错误路径测试."""

    def _make_agent(self):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_ask_checkpoint_question_raises_on_empty(self):
        """测试 checkpoint 提问空内容时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""
        with pytest.raises(RuntimeError, match="空内容"):
            agent.ask_checkpoint_question()

    def test_ask_discussion_question_raises_on_empty(self):
        """测试讨论提问空内容时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""
        with pytest.raises(RuntimeError, match="空内容"):
            agent.ask_discussion_question()

    def test_reply_to_student_raises_on_empty(self):
        """测试回复学生空内容时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""
        with pytest.raises(RuntimeError, match="空内容"):
            agent.reply_to_student(student_name="张三", student_message="回答内容")

    def test_assign_homework_raises_on_empty(self):
        """测试布置作业空内容时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""
        with pytest.raises(RuntimeError, match="空内容"):
            agent.assign_homework()

    def test_grade_homework_raises_on_empty(self):
        """测试作业评分空内容时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""
        with pytest.raises(RuntimeError, match="空内容"):
            agent.grade_homework(student_name="张三", homework_content="作业")

    def test_end_feedback_raises_on_empty(self):
        """测试课程总结空内容时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""
        with pytest.raises(RuntimeError, match="空内容"):
            agent.end_feedback()

    def test_ask_checkpoint_question_no_record_on_empty(self):
        """测试 checkpoint 提问空内容时不记录消息."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""
        with pytest.raises(RuntimeError):
            agent.ask_checkpoint_question()
        assert len(agent.session_memory.message_history) == 0
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentNewMethodsErrors -v`
Expected: 7 passed

- [ ] **Step 3: Run full test suite**

Run: `cd /Users/pangzerui/SSPU/ai\ lab/教学智能体/project/backend && python -m pytest tests/units/ -v`
Expected: All 206 tests pass

- [ ] **Step 4: Commit**

```bash
cd "/Users/pangzerui/SSPU/ai lab/教学智能体/project"
git add backend/tests/units/test_teacher_agent.py
git commit -m "test(teacher-agent): add error path tests for new teaching mode methods"
```

---

## Self-Review

### 1. Spec coverage

| 设计文档要求 | 对应 Task |
|-------------|----------|
| 灌输式 system prompt | 已有（Phase 5 `_MODE_INSTRUCTIONS["didactic"]`） |
| 启发式 system prompt | 已有（Phase 5 `_MODE_INSTRUCTIONS["heuristic"]`） |
| 讨论式 system prompt | 已有（Phase 5 `_MODE_INSTRUCTIONS["discussion"]`） |
| 启发式: `ask_checkpoint_question()` | Task 1 |
| 讨论式: `ask_discussion_question()` | Task 2 |
| 教师回复学生: `reply_to_student()` | Task 3 |
| 布置作业: `assign_homework()` | Task 4 |
| 作业评分: `grade_homework()` (LLM评价) | Task 5 |
| 课程反馈: `end_feedback()` | Task 6 |
| MemoryManager 处理新消息类型 | Task 7 |
| 灌输式无互动提问 | 已满足（orchestrator 不调用 question 方法） |
| 三种模式温度差异化 | 已有（`_get_mode_temperature()`） |

### 2. Placeholder scan

- 无 TBD、TODO、fill in details
- 所有测试包含完整代码
- 所有实现步骤包含完整代码
- 无 "similar to Task N" 引用

### 3. Type consistency

- `_record_message(content: str, message_type: MessageType)` — 所有 Task 一致使用
- `MessageType.CHECKPOINT_QUESTION` — Task 1 和 Task 2 一致
- `MessageType.TEACHER_REPLY` — Task 3 使用
- `MessageType.ASSIGN_HOMEWORK` — Task 4 使用
- `MessageType.HOMEWORK_FEEDBACK` — Task 5 使用
- `MessageType.END_FEEDBACK` — Task 6 使用
- 空内容检查模式 `if not content or not content.strip()` — 所有方法一致
- `safe_llm_call` 调用签名一致：`(self.llm.invoke, "教师", description, messages, temperature=...)`

### 4. 设计文档中 `collect_feedback()` 说明

路线图中列出了 `collect_feedback()`。这不是 TeacherAgent 的方法 — 它是一个由 Phase 7 编排器处理的工作流程（编排器调用 `StudentAgent.give_feedback()`）。所以这里不需要 TeacherAgent 方法。StudentAgent 已经有了 `give_feedback()` 方法（Phase 5）。

### 5. 预计测试计数

| Task | 新增测试 | 累计 |
|------|---------|------|
| Task 1 | 5 | 165 |
| Task 2 | 5 | 170 |
| Task 3 | 5 | 175 |
| Task 4 | 4 | 179 |
| Task 5 | 5 | 184 |
| Task 6 | 4 | 188 |
| Task 7 | 5 | 193 |
| Task 9 | 7 | 200 |
| **Total** | **40** | **200** |
