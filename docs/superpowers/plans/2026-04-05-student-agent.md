# 学生 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现学生 Agent（StudentAgent），支持回答教师问题、主动提问、提交作业和课堂反馈，回答质量和行为模式受 level/attitude/learning_ability 参数影响。

**Architecture:** StudentAgent 类与 TeacherAgent 对称设计，接收 StudentProfile、SessionMemory、LLM 和 MemoryManager。通过构建学生角色 system prompt 调用 LLM 生成回答，回答质量受学生参数影响。should_respond() 基于态度概率判断是否主动响应。

**Tech Stack:** Python 3.12+, LangChain (ChatOpenAI via LLMClient), Pydantic, pytest, unittest.mock

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/agents/student_agent.py` | 修改 | StudentAgent 类（初始化、回答、提问、作业、反馈、should_respond） |
| `backend/tests/units/test_student_agent.py` | 新建 | StudentAgent 全部单元测试 |

---

## 已有代码依赖（不需要修改）

- `backend/schemas/message.py` — MessageType 枚举（ANSWER_TO_CHECKPOINT, QUESTION_TO_TEACHER, HOMEWORK_SUBMISSION, FEEDBACK_SUBMISSION, REPLY_TO_TEACHER）
- `backend/schemas/student.py` — StudentProfile, StudentLevel, StudentAttitude
- `backend/agents/memories/student_memory.py` — StudentAgentMemory（from_profile, get_system_prompt_addition, update_knowledge）
- `backend/agents/memories/memory_manager.py` — MemoryManager（register_student, process_message）
- `backend/core/llm_client.py` — LLMClient（invoke, stream）

---

## 设计决策

1. **不使用 MemoryAwareStudentAgent（LangChain AgentExecutor）**：与 TeacherAgent 一致，直接使用 LLMClient 调用 LLM，不引入 AgentExecutor 的复杂性。
2. **should_respond() 使用确定性概率**：积极 80%、中性 50%、消极 20%，测试时通过 `rng` 参数控制。
3. **回答质量通过 system prompt 控制**：不同 level/attitude 的学生有不同的 system prompt 指令，LLM 据此生成不同质量的回答。
4. **温度固定**：学生回答使用固定温度 0.7（与讨论式教学一致），因为回答需要一定的多样性。
5. **测试数据使用 Python 基础**：与 TeacherAgent 测试保持一致。

---

### Task 1: StudentAgent 基础结构和初始化

**Files:**
- Modify: `backend/agents/student_agent.py`
- Test: `backend/tests/units/test_student_agent.py`

- [ ] **Step 1: 写失败测试 — 初始化和参数校验**

```python
# backend/tests/units/test_student_agent.py
"""StudentAgent 单元测试."""

import random
from unittest.mock import MagicMock

from schemas.student import StudentProfile


class TestStudentAgentInit:
    """StudentAgent 初始化测试."""

    def test_init_with_required_params(self):
        """测试使用必需参数初始化."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(name="张三", learning_ability=7)
        mock_llm = MagicMock()

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

        assert agent.profile is profile
        assert agent.profile.name == "张三"
        assert agent.session_memory is session_mem
        assert agent.llm is mock_llm

    def test_init_creates_memory_from_profile(self):
        """测试从 StudentProfile 创建 StudentAgentMemory."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(
            name="李四",
            level="excellent",
            attitude="active",
            learning_ability=9,
        )
        mock_llm = MagicMock()

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

        assert agent.memory.name == "李四"
        assert agent.memory.level.value == "excellent"
        assert agent.memory.attitude.value == "active"
        assert agent.memory.learning_ability == 9

    def test_init_with_existing_memory(self):
        """测试使用已有的 StudentAgentMemory 初始化."""
        from agents.memories import SessionMemory
        from agents.memories.student_memory import StudentAgentMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(name="王五", learning_ability=5)
        mock_llm = MagicMock()

        existing_memory = StudentAgentMemory(
            name="王五",
            learned_concepts=["变量"],
            current_knowledge_level=0.3,
        )

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
            memory=existing_memory,
        )

        assert "等式性质" in agent.memory.learned_concepts
        assert agent.memory.current_knowledge_level == 0.3

    def test_init_with_rng(self):
        """测试使用自定义 rng 初始化."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(name="赵六", learning_ability=5)
        mock_llm = MagicMock()
        test_rng = random.Random(42)

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
            rng=test_rng,
        )

        assert agent.rng is test_rng
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentInit -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.student_agent'` 或 `ImportError`

- [ ] **Step 3: 实现 StudentAgent 初始化**

```python
# backend/agents/student_agent.py
"""学生 Agent - 负责回答问题和互动."""

from __future__ import annotations

import random

from agents.memories import SessionMemory
from agents.memories.student_memory import StudentAgentMemory
from schemas.student import StudentProfile


class StudentAgent:
    """学生 Agent - 负责回答问题和互动."""

    def __init__(
        self,
        *,
        session_memory: SessionMemory,
        llm,
        profile: StudentProfile,
        memory: StudentAgentMemory | None = None,
        rng: random.Random | None = None,
    ) -> None:
        """初始化学生 Agent.

        Args:
            session_memory: 会话记忆
            llm: LLM 客户端（需实现 invoke(prompt) -> str 接口）
            profile: 学生配置
            memory: 已有的 StudentAgentMemory（可选）
            rng: 随机数生成器（可选，用于测试确定性）
        """
        self.session_memory = session_memory
        self.llm = llm
        self.profile = profile
        self.rng = rng or random.Random()

        self.memory = memory or StudentAgentMemory.from_profile(profile)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentInit -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/agents/student_agent.py backend/tests/units/test_student_agent.py
git commit -m "feat: add StudentAgent initialization with profile and memory support"
```

---

### Task 2: should_respond() 判断逻辑

**Files:**
- Modify: `backend/agents/student_agent.py`
- Modify: `backend/tests/units/test_student_agent.py`

- [ ] **Step 1: 写失败测试 — should_respond 基于态度概率判断**

```python
# 追加到 backend/tests/units/test_student_agent.py

class TestStudentAgentShouldRespond:
    """StudentAgent should_respond 测试."""

    def _make_agent(self, *, attitude: str = "neutral", rng_seed: int = 42):
        """辅助方法：创建 StudentAgent."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(name="测试学生", attitude=attitude, learning_ability=5)
        mock_llm = MagicMock()
        test_rng = random.Random(rng_seed)

        return StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
            rng=test_rng,
        )

    def test_active_student_responds_most_of_the_time(self):
        """测试积极学生大概率响应."""
        agent = self._make_agent(attitude="active", rng_seed=42)

        results = [agent.should_respond() for _ in range(100)]
        respond_rate = sum(results) / len(results)

        assert respond_rate > 0.6  # 积极学生响应率应 > 60%

    def test_neutral_student_responds_half_the_time(self):
        """测试中性学生约 50% 响应."""
        agent = self._make_agent(attitude="neutral", rng_seed=42)

        results = [agent.should_respond() for _ in range(100)]
        respond_rate = sum(results) / len(results)

        assert 0.3 < respond_rate < 0.7  # 中性学生响应率约 50%

    def test_passive_student_responds_less(self):
        """测试消极学生响应较少."""
        agent = self._make_agent(attitude="passive", rng_seed=42)

        results = [agent.should_respond() for _ in range(100)]
        respond_rate = sum(results) / len(results)

        assert respond_rate < 0.4  # 消极学生响应率应 < 40%

    def test_should_respond_returns_boolean(self):
        """测试 should_respond 返回布尔值."""
        agent = self._make_agent()

        result = agent.should_respond()

        assert isinstance(result, bool)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentShouldRespond -v`
Expected: FAIL — `AttributeError: 'StudentAgent' object has no attribute 'should_respond'`

- [ ] **Step 3: 实现 should_respond()**

在 `StudentAgent` 类中添加：

```python
    # 态度 → 响应概率
    _RESPOND_PROBABILITIES = {
        "active": 0.8,
        "neutral": 0.5,
        "passive": 0.2,
    }

    def should_respond(self) -> bool:
        """判断学生是否应该响应（基于态度概率）.

        Returns:
            True 表示学生选择响应
        """
        probability = self._RESPOND_PROBABILITIES.get(
            self.profile.attitude.value, 0.5
        )
        return self.rng.random() < probability
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentShouldRespond -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/agents/student_agent.py backend/tests/units/test_student_agent.py
git commit -m "feat: add should_respond() with attitude-based probability"
```

---

### Task 3: answer_question() 回答教师问题

**Files:**
- Modify: `backend/agents/student_agent.py`
- Modify: `backend/tests/units/test_student_agent.py`

- [ ] **Step 1: 写失败测试 — answer_question 调用 LLM 并记录消息**

```python
# 追加到 backend/tests/units/test_student_agent.py

class TestStudentAgentAnswerQuestion:
    """StudentAgent answer_question 测试."""

    def _make_agent(self, *, level: str = "average", attitude: str = "neutral"):
        """辅助方法：创建 StudentAgent."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(
            name="张三",
            level=level,
            attitude=attitude,
            learning_ability=6,
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "Python中的变量用来存储数据，可以用等号赋值。"

        return StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

    def test_answer_question_calls_llm(self):
        """测试 answer_question 调用 LLM."""
        agent = self._make_agent()

        agent.answer_question("什么是Python变量？")

        assert agent.llm.invoke.called

    def test_answer_question_includes_question_in_prompt(self):
        """测试 answer_question 在 prompt 中包含教师问题."""
        agent = self._make_agent()

        agent.answer_question("什么是Python变量？")

        messages = agent.llm.invoke.call_args[0][0]
        # 找到包含问题的 user message
        user_msg = messages[-1]["content"]
        assert "Python" in user_msg

    def test_answer_question_includes_student_context(self):
        """测试 answer_question 的 system prompt 包含学生上下文."""
        agent = self._make_agent()

        agent.answer_question("如何定义一个Python函数？")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "张三" in system_msg  # 学生名字
        assert "Python基础" in system_msg  # 教学主题

    def test_answer_question_excellent_student_has_higher_quality_prompt(self):
        """测试优秀学生的 prompt 包含更高质量要求."""
        agent = self._make_agent(level="excellent")

        agent.answer_question("如何定义一个Python函数？")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "优秀" in system_msg

    def test_answer_question_basic_student_has_basic_prompt(self):
        """测试基础学生的 prompt 包含基础水平描述."""
        agent = self._make_agent(level="basic")

        agent.answer_question("如何定义一个Python函数？")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "基础" in system_msg

    def test_answer_question_returns_llm_response(self):
        """测试 answer_question 返回 LLM 响应."""
        agent = self._make_agent()

        result = agent.answer_question("什么是Python变量？")

        assert result == "Python中的变量用来存储数据，可以用等号赋值。"

    def test_answer_question_records_message_in_session_memory(self):
        """测试 answer_question 将消息记录到会话记忆."""
        agent = self._make_agent()

        agent.answer_question("什么是Python变量？")

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "张三"
        assert msg.message_type.value == "answer_to_checkpoint"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentAnswerQuestion -v`
Expected: FAIL — `AttributeError: 'StudentAgent' object has no attribute 'answer_question'`

- [ ] **Step 3: 实现 answer_question()**

在 `StudentAgent` 类中添加：

```python
    from datetime import datetime

    from agents.memories.memory_manager import MemoryManager
    from schemas.message import Message, MessageType

    def _build_system_prompt(self) -> str:
        """构建学生 system prompt.

        根据学生的 level 和 attitude 生成角色化提示。
        """
        topic = self.session_memory.topic
        student_context = self.memory.get_system_prompt_addition(topic)
        context = self.session_memory.get_agent_context()

        level_instructions = {
            "excellent": (
                "- 你的回答应该准确、有条理，能举一反三\n"
                "- 你能正确使用专业概念和术语\n"
                "- 你能从多个角度分析问题\n"
            ),
            "average": (
                "- 你的回答基本正确，但可能不够深入\n"
                "- 你对一些概念可能有些模糊\n"
                "- 你能解决基本问题，复杂问题可能出错\n"
            ),
            "basic": (
                "- 你的回答可能不够准确，有时会混淆概念\n"
                "- 你对基础概念的理解不够牢固\n"
                "- 你可能会犯一些常见的错误\n"
            ),
        }

        level_section = level_instructions.get(
            self.profile.level.value, level_instructions["average"]
        )

        return f"""{student_context}

{level_section}
{context}
"""

    def answer_question(self, question: str) -> str:
        """回答教师的问题.

        Args:
            question: 教师提出的问题

        Returns:
            学生的回答文本
        """
        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        content = self.llm.invoke(messages)

        # 记录消息到会话记忆
        message = Message(
            sender=self.profile.name,
            message_type=MessageType.ANSWER_TO_CHECKPOINT,
            content=content,
            timestamp=datetime.now(),
        )
        self.session_memory.add_message(message)

        return content
```

注意：需要在文件顶部添加 `from datetime import datetime` 导入。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentAnswerQuestion -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add backend/agents/student_agent.py backend/tests/units/test_student_agent.py
git commit -m "feat: add answer_question() with level-aware system prompt"
```

---

### Task 4: ask_question() 学生主动提问

**Files:**
- Modify: `backend/agents/student_agent.py`
- Modify: `backend/tests/units/test_student_agent.py`

- [ ] **Step 1: 写失败测试 — ask_question 调用 LLM 生成问题**

```python
# 追加到 backend/tests/units/test_student_agent.py

class TestStudentAgentAskQuestion:
    """StudentAgent ask_question 测试."""

    def _make_agent(self, *, attitude: str = "neutral"):
        """辅助方法：创建 StudentAgent."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(
            name="李四",
            attitude=attitude,
            learning_ability=5,
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "老师，列表和元组有什么区别？"

        return StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

    def test_ask_question_calls_llm(self):
        """测试 ask_question 调用 LLM."""
        agent = self._make_agent()

        agent.ask_question("刚才讲的列表操作")

        assert agent.llm.invoke.called

    def test_ask_question_includes_teaching_context(self):
        """测试 ask_question 的 prompt 包含教学内容上下文."""
        agent = self._make_agent()

        agent.ask_question("刚才讲的列表操作")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "Python基础" in system_msg
        assert "李四" in system_msg

    def test_ask_question_returns_question_text(self):
        """测试 ask_question 返回问题文本."""
        agent = self._make_agent()

        result = agent.ask_question("列表操作")

        assert result == "老师，列表和元组有什么区别？"

    def test_ask_question_records_message(self):
        """测试 ask_question 记录消息到会话记忆."""
        agent = self._make_agent()

        agent.ask_question("列表操作")

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "李四"
        assert msg.message_type.value == "question_to_teacher"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentAskQuestion -v`
Expected: FAIL — `AttributeError: 'StudentAgent' object has no attribute 'ask_question'`

- [ ] **Step 3: 实现 ask_question()**

在 `StudentAgent` 类中添加：

```python
    def ask_question(self, teaching_context: str) -> str:
        """基于困惑点向教师提问.

        Args:
            teaching_context: 最近的教学内容上下文（触发提问的原因）

        Returns:
            学生提出的问题
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            f"基于以下教学内容，请以学生的身份提出一个你不理解的问题。\n"
            f"教学内容: {teaching_context}\n"
            f"要求: 提问要具体、自然，符合你的学习水平和当前知识掌握程度。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = self.llm.invoke(messages)

        # 记录消息
        message = Message(
            sender=self.profile.name,
            message_type=MessageType.QUESTION_TO_TEACHER,
            content=content,
            timestamp=datetime.now(),
        )
        self.session_memory.add_message(message)

        return content
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentAskQuestion -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add backend/agents/student_agent.py backend/tests/units/test_student_agent.py
git commit -m "feat: add ask_question() for student-initiated questions"
```

---

### Task 5: submit_homework() 提交作业

**Files:**
- Modify: `backend/agents/student_agent.py`
- Modify: `backend/tests/units/test_student_agent.py`

- [ ] **Step 1: 写失败测试 — submit_homework 生成作业提交**

```python
# 追加到 backend/tests/units/test_student_agent.py

class TestStudentAgentSubmitHomework:
    """StudentAgent submit_homework 测试."""

    def _make_agent(self, *, level: str = "average", learning_ability: int = 5):
        """辅助方法：创建 StudentAgent."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(
            name="王五",
            level=level,
            learning_ability=learning_ability,
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = (
            "def calculate_average(numbers):\n"
            "    return sum(numbers) / len(numbers)"
        )

        return StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

    def test_submit_homework_calls_llm(self):
        """测试 submit_homework 调用 LLM."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        assert agent.llm.invoke.called

    def test_submit_homework_includes_homework_prompt(self):
        """测试 submit_homework 的 prompt 包含作业要求."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[-1]["content"]

        assert "平均" in user_msg

    def test_submit_homework_includes_student_context(self):
        """测试 submit_homework 的 system prompt 包含学生上下文."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "王五" in system_msg

    def test_submit_homework_returns_response(self):
        """测试 submit_homework 返回 LLM 响应."""
        agent = self._make_agent()

        result = agent.submit_homework("写一个函数计算列表的平均值")

        assert "def" in result

    def test_submit_homework_records_message(self):
        """测试 submit_homework 记录消息."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "王五"
        assert msg.message_type.value == "homework_submission"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentSubmitHomework -v`
Expected: FAIL — `AttributeError: 'StudentAgent' object has no attribute 'submit_homework'`

- [ ] **Step 3: 实现 submit_homework()**

在 `StudentAgent` 类中添加：

```python
    def submit_homework(self, homework_prompt: str) -> str:
        """提交作业.

        Args:
            homework_prompt: 作业题目/要求

        Returns:
            学生的作业回答
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            f"请完成以下作业：\n\n{homework_prompt}\n\n"
            f"要求: 根据你已学到的知识完成作业，展示你的解题过程。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = self.llm.invoke(messages)

        # 记录消息
        message = Message(
            sender=self.profile.name,
            message_type=MessageType.HOMEWORK_SUBMISSION,
            content=content,
            timestamp=datetime.now(),
        )
        self.session_memory.add_message(message)

        return content
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentSubmitHomework -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/agents/student_agent.py backend/tests/units/test_student_agent.py
git commit -m "feat: add submit_homework() for homework submission"
```

---

### Task 6: give_feedback() 课堂反馈

**Files:**
- Modify: `backend/agents/student_agent.py`
- Modify: `backend/tests/units/test_student_agent.py`

- [ ] **Step 1: 写失败测试 — give_feedback 生成课堂反馈**

```python
# 追加到 backend/tests/units/test_student_agent.py

class TestStudentAgentGiveFeedback:
    """StudentAgent give_feedback 测试."""

    def _make_agent(self, *, attitude: str = "neutral"):
        """辅助方法：创建 StudentAgent."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(
            name="赵六",
            attitude=attitude,
            learning_ability=6,
        )
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = (
            "今天的课我学到了列表操作，但对列表推导式还不太理解。"
        )

        return StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

    def test_give_feedback_calls_llm(self):
        """测试 give_feedback 调用 LLM."""
        agent = self._make_agent()

        agent.give_feedback()

        assert agent.llm.invoke.called

    def test_give_feedback_includes_feedback_prompt(self):
        """测试 give_feedback 的 prompt 包含反馈请求."""
        agent = self._make_agent()

        agent.give_feedback()

        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[-1]["content"]

        assert "反馈" in user_msg or "总结" in user_msg

    def test_give_feedback_includes_student_context(self):
        """测试 give_feedback 的 system prompt 包含学生上下文."""
        agent = self._make_agent()

        agent.give_feedback()

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "赵六" in system_msg
        assert "Python基础" in system_msg

    def test_give_feedback_returns_response(self):
        """测试 give_feedback 返回反馈文本."""
        agent = self._make_agent()

        result = agent.give_feedback()

        assert "列表操作" in result

    def test_give_feedback_records_message(self):
        """测试 give_feedback 记录消息."""
        agent = self._make_agent()

        agent.give_feedback()

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "赵六"
        assert msg.message_type.value == "feedback_submission"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentGiveFeedback -v`
Expected: FAIL — `AttributeError: 'StudentAgent' object has no attribute 'give_feedback'`

- [ ] **Step 3: 实现 give_feedback()**

在 `StudentAgent` 类中添加：

```python
    def give_feedback(self) -> str:
        """对课程给出总结性反馈.

        Returns:
            学生的课程反馈文本
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            "课程即将结束，请对今天的学习进行总结和反馈。\n"
            "请包含以下内容：\n"
            "1. 你学到了什么\n"
            "2. 你还有什么不理解的地方\n"
            "3. 你对课程的感受\n\n"
            "要求: 以自然的学生口吻回答，内容符合你的学习水平。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = self.llm.invoke(messages)

        # 记录消息
        message = Message(
            sender=self.profile.name,
            message_type=MessageType.FEEDBACK_SUBMISSION,
            content=content,
            timestamp=datetime.now(),
        )
        self.session_memory.add_message(message)

        return content
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py::TestStudentAgentGiveFeedback -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add backend/agents/student_agent.py backend/tests/units/test_student_agent.py
git commit -m "feat: add give_feedback() for course feedback"
```

---

### Task 7: 运行全部测试和 lint 检查

**Files:**
- 无新建/修改

- [ ] **Step 1: 运行全部 StudentAgent 测试**

Run: `cd backend && python -m pytest tests/units/test_student_agent.py -v`
Expected: 25 passed (4 init + 4 should_respond + 7 answer_question + 4 ask_question + 5 submit_homework + 5 give_feedback - 1 = 29)

Wait, let me count: 4 + 4 + 7 + 4 + 5 + 5 = 29 tests

Expected: 29 passed

- [ ] **Step 2: 运行全部后端测试确保无回归**

Run: `cd backend && python -m pytest tests/ -v`
Expected: 所有测试通过（包括之前 133 个 + 新增 29 个）

- [ ] **Step 3: 运行 ruff 检查**

Run: `cd backend && ruff check agents/student_agent.py tests/units/test_student_agent.py`
Expected: 无错误

- [ ] **Step 4: 运行 ruff 格式化**

Run: `cd backend && ruff format agents/student_agent.py tests/units/test_student_agent.py`
Expected: 无变更或自动格式化

- [ ] **Step 5: Commit（如有 lint 修复）**

```bash
git add -A
git commit -m "chore: fix lint issues in student_agent"
```

---

### Task 8: 添加真实 LLM 集成测试（可选）

**Files:**
- Modify: `backend/tests/integration/test_teacher_agent_real.py`（参考模式）
- Test: `backend/tests/integration/test_student_agent_real.py`

- [ ] **Step 1: 写集成测试 — 使用真实 LLM 测试 StudentAgent**

```python
# backend/tests/integration/test_student_agent_real.py
"""StudentAgent 真实 LLM 集成测试."""

import os

import pytest

from schemas.student import StudentProfile


@pytest.mark.integration
class TestStudentAgentReal:
    """使用真实 LLM API 测试 StudentAgent."""

    def _make_agent(self, *, name="集成测试学生", level="average", attitude="neutral"):
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent
        from core.llm_client import LLMClient

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(
            name=name,
            level=level,
            attitude=attitude,
            learning_ability=6,
        )

        llm = LLMClient.from_config()

        return StudentAgent(
            session_memory=session_mem,
            llm=llm,
            profile=profile,
        )

    def test_answer_question_real_llm(self):
        """测试使用真实 LLM 回答问题."""
        agent = self._make_agent()

        response = agent.answer_question("什么是Python变量？")

        print(f"\n=== {agent.profile.name} 回答 ===")
        print(response)
        print("=" * 40)

        assert len(response) > 10
        assert "变量" in response

    def test_ask_question_real_llm(self):
        """测试使用真实 LLM 主动提问."""
        agent = self._make_agent(attitude="active")

        response = agent.ask_question("列表推导式：用简洁的语法从已有列表生成新列表")

        print(f"\n=== {agent.profile.name} 提问 ===")
        print(response)
        print("=" * 40)

        assert len(response) > 5

    def test_submit_homework_real_llm(self):
        """测试使用真实 LLM 提交作业."""
        agent = self._make_agent(level="excellent")

        response = agent.submit_homework("写一个函数：判断一个字符串是否为回文")

        print(f"\n=== {agent.profile.name} 作业 ===")
        print(response)
        print("=" * 40)

        assert len(response) > 10

    def test_give_feedback_real_llm(self):
        """测试使用真实 LLM 提交课程反馈."""
        agent = self._make_agent()

        response = agent.give_feedback()

        print(f"\n=== {agent.profile.name} 反馈 ===")
        print(response)
        print("=" * 40)

        assert len(response) > 10
```

- [ ] **Step 2: 运行集成测试**

Run: `cd backend && python -m pytest tests/integration/test_student_agent_real.py -v -s`
Expected: 4 passed（需要网络和 API key）

- [ ] **Step 3: 运行跳过集成测试的单元测试**

Run: `cd backend && python -m pytest tests/ -v -m "not integration"`
Expected: 所有单元测试通过

- [ ] **Step 4: Commit**

```bash
git add backend/tests/integration/test_student_agent_real.py
git commit -m "test: add real LLM integration tests for StudentAgent"
```

---

## Self-Review 检查

### Spec 覆盖检查

| Phase 5 需求 | 对应 Task |
|-------------|----------|
| StudentAgent 基础结构 | Task 1 |
| answer_question() 基于 level 差异化 | Task 3 |
| should_respond() 基于 attitude 判断 | Task 2 |
| ask_question() 主动提问 | Task 4 |
| submit_homework() 提交作业 | Task 5 |
| give_feedback() 课程反馈 | Task 6 |
| 全部测试通过 + lint | Task 7 |
| 真实 LLM 集成测试 | Task 8 |

### Placeholder 扫描

- 无 TBD、TODO、"implement later"
- 所有测试包含完整代码
- 所有步骤有精确命令和预期输出

### 类型一致性检查

- `MessageType.ANSWER_TO_CHECKPOINT` — 在 schemas/message.py 中已定义
- `MessageType.QUESTION_TO_TEACHER` — 在 schemas/message.py 中已定义
- `MessageType.HOMEWORK_SUBMISSION` — 在 schemas/message.py 中已定义
- `MessageType.FEEDBACK_SUBMISSION` — 在 schemas/message.py 中已定义
- `StudentAgentMemory.from_profile()` — 在 student_memory.py 中已实现
- `StudentAgentMemory.get_system_prompt_addition()` — 在 student_memory.py 中已实现
- `SessionMemory.add_message()` — 使用的是 session_memory 的方法（需确认）
- `SessionMemory.get_agent_context()` — 在 session_memory.py 中已实现
