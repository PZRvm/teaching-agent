# 教师 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 实现教师 Agent，能够使用硅基流动 LLM API 对指定主题进行讲授，支持不同教学模式的差异化讲授风格，并与 MemoryManager 完整集成。

**架构:** `TeacherAgent` 类封装 `ChatOpenAI`（通过可复用的 LLM 客户端）和 `MemoryManager`。每次 `deliver_lecture()` 调用通过 LLM 生成模式特定的讲授内容，然后通过 `MemoryManager` 记录消息以更新教师和学生记忆。Agent 使用可注入的 LLM 函数进行知识点提取和内容完成判断。

**技术栈:** Python 3.12+, langchain-openai (ChatOpenAI), Pydantic, 现有 MemoryManager 系统

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/core/llm_client.py` | 可复用的 LLM 客户端，封装 ChatOpenAI，API key 从 `.env` 读取，其余参数从 `configs/llm.yml` 读取 |
| `backend/agents/teacher_agent.py` | TeacherAgent 类：初始化、system prompt、deliver_lecture、is_content_complete |
| `backend/tests/units/test_llm_client.py` | LLM 客户端单元测试（模拟 API） |
| `backend/tests/units/test_teacher_agent.py` | TeacherAgent 单元测试（模拟 LLM + 记忆系统） |

---

### 任务 1: LLM 客户端

**文件:**
- 创建: `backend/core/llm_client.py`
- 创建: `backend/tests/units/test_llm_client.py`

- [ ] **步骤 1: 编写失败测试**

```python
# backend/tests/units/test_llm_client.py
"""LLM Client 单元测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestLLMClient:
    """LLM Client 测试."""

    def test_init_uses_config(self):
        """测试使用配置初始化."""
        from core.llm_client import LLMClient

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
            temperature=0.5,
            max_tokens=1000,
        )

        assert client.model == "test-model"
        assert client.temperature == 0.5
        assert client.max_tokens == 1000

    def test_init_from_config_uses_env_api_key(self):
        """测试 from_config() 从 .env 读取 API key."""
        from core.llm_client import LLMClient

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-env-key"}):
            client = LLMClient.from_config()

        assert client.api_key == "test-env-key"
        assert client.base_url == "https://api.siliconflow.cn/v1"
        assert client.model == "Qwen/Qwen2.5-7B-Instruct"

    def test_invoke_returns_response(self):
        """测试 invoke 调用 LLM 并返回响应."""
        from core.llm_client import LLMClient

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
        )

        mock_response = MagicMock()
        mock_response.content = "这是讲授内容"

        client._llm = MagicMock(return_value=mock_response)
        result = client.invoke("请讲授Python变量")

        assert result == "这是讲授内容"

    def test_invoke_with_messages(self):
        """测试 invoke 传入消息列表."""
        from core.llm_client import LLMClient
        from langchain_core.messages import HumanMessage, SystemMessage

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
        )

        mock_response = MagicMock()
        mock_response.content = "响应内容"

        client._llm = MagicMock(return_value=mock_response)

        messages = [
            SystemMessage(content="你是教师"),
            HumanMessage(content="请讲授变量"),
        ]
        result = client.invoke(messages)

        assert result == "响应内容"

    def test_invoke_with_temperature_override(self):
        """测试 invoke 支持临时覆盖 temperature."""
        from core.llm_client import LLMClient

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
            temperature=0.7,
        )

        mock_response = MagicMock()
        mock_response.content = "响应"

        client._llm = MagicMock(return_value=mock_response)
        client.invoke("test", temperature=0.1)

        client._llm.invoke.assert_called_once()
        call_kwargs = client._llm.invoke.call_args
        assert call_kwargs[1].get("temperature") == 0.1
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_llm_client.py -v`
预期: FAIL，报错 `ModuleNotFoundError: No module named 'core.llm_client'`

- [ ] **步骤 3: 编写最小实现**

```python
# backend/core/llm_client.py
"""LLM 客户端 - 封装 langchain_openai ChatOpenAI."""

from __future__ import annotations

from langchain_openai import ChatOpenAI


class LLMClient:
    """可复用的 LLM 客户端."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> None:
        """初始化 LLM 客户端.

        Args:
            base_url: API 地址
            api_key: API 密钥
            model: 模型名称
            temperature: 采样温度
            max_tokens: 最大 token 数
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @classmethod
    def from_config(cls) -> LLMClient:
        """从 .env 和 YAML 配置文件创建实例.

        API key 从 .env 环境变量 OPENAI_API_KEY 读取，
        其余参数从 configs/llm.yml 读取。

        Returns:
            LLMClient 实例
        """
        import os

        import yaml

        from pathlib import Path

        config_path = Path(__file__).parents[1] / "configs" / "llm.yml"
        with open(config_path) as f:
            llm_config = yaml.safe_load(f)

        api_key = os.environ.get("OPENAI_API_KEY", llm_config["llm"].get("api_key", ""))

        return cls(
            base_url=llm_config["llm"]["base_url"],
            api_key=api_key,
            model=llm_config["llm"]["model"],
            temperature=llm_config["llm"]["temperature"],
            max_tokens=llm_config["llm"]["max_tokens"],
        )

    def invoke(
        self,
        prompt: str | list,
        temperature: float | None = None,
    ) -> str:
        """调用 LLM 生成响应.

        Args:
            prompt: 提示文本或消息列表
            temperature: 可选温度覆盖

        Returns:
            LLM 响应文本
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        if isinstance(prompt, str):
            messages = [HumanMessage(content=prompt)]
        else:
            messages = prompt

        invoke_kwargs: dict = {"input": messages}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature

        response = self._llm.invoke(**invoke_kwargs)
        return response.content
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_llm_client.py -v`
预期: 全部 5 个测试通过

- [ ] **步骤 5: 提交**

```bash
git add backend/core/llm_client.py backend/tests/units/test_llm_client.py
git commit -m "feat: add LLM client wrapping ChatOpenAI with YAML config"
```

---

### 任务 2: TeacherAgent 基础结构

**文件:**
- 修改: `backend/agents/teacher_agent.py`
- 创建: `backend/tests/units/test_teacher_agent.py`

- [ ] **步骤 1: 编写失败测试**

```python
# backend/tests/units/test_teacher_agent.py
"""TeacherAgent 单元测试."""

from datetime import datetime
from unittest.mock import MagicMock

from schemas.message import Message, MessageType
from schemas.student import StudentLevel, StudentProfile


class TestTeacherAgentInit:
    """TeacherAgent 初始化测试."""

    def test_init_with_memory_manager(self):
        """测试使用 MemoryManager 初始化."""
        from agents.memories import SessionMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_llm = MagicMock()

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
        )

        assert agent.session_memory is session_mem
        assert agent.teaching_mode == "didactic"
        assert agent.llm is mock_llm

    def test_init_default_teaching_mode(self):
        """测试默认教学模式为 didactic."""
        from agents.memories import SessionMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_llm = MagicMock()

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
        )

        assert agent.teaching_mode == "didactic"

    def test_init_registers_students(self):
        """测试初始化时注册学生到 MemoryManager."""
        from agents.memories import SessionMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_llm = MagicMock()

        profiles = [
            StudentProfile(name="张三", learning_ability=8),
            StudentProfile(name="李四", learning_ability=5),
        ]

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            students=profiles,
        )

        assert "张三" in agent.memory_manager.student_memories
        assert "李四" in agent.memory_manager.student_memories

    def test_init_with_memory_manager(self):
        """测试使用已有的 MemoryManager 初始化."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("已有知识点")

        from agents.memories.memory_manager import MemoryManager

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)

        mock_llm = MagicMock()
        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            memory_manager=mm,
        )

        assert "已有知识点" in agent.memory_manager.teacher_memory.covered_topics
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentInit -v`
预期: FAIL，报错 `ModuleNotFoundError: No module named 'agents.teacher_agent'`（或 ImportError）

- [ ] **步骤 3: 编写最小实现**

```python
# backend/agents/teacher_agent.py
"""教师 Agent - 负责讲授内容生成和教学控制."""

from __future__ import annotations

from datetime import datetime

from schemas.message import Message, MessageType
from schemas.student import StudentProfile

from agents.memories import SessionMemory, StudentAgentMemory
from agents.memories.memory_manager import MemoryManager


class TeacherAgent:
    """教师 Agent - 负责讲授内容生成和教学控制."""

    def __init__(
        self,
        *,
        session_memory: SessionMemory,
        llm,
        teaching_mode: str = "didactic",
        students: list[StudentProfile] | None = None,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        """初始化教师 Agent.

        Args:
            session_memory: 会话记忆
            llm: LLM 客户端（需实现 invoke(prompt) -> str 接口）
            teaching_mode: 教学模式（didactic/heuristic/discussion）
            students: 学生配置列表
            memory_manager: 已有的 MemoryManager（可选）
        """
        self.session_memory = session_memory
        self.teaching_mode = teaching_mode
        self.llm = llm

        if memory_manager is not None:
            self.memory_manager = memory_manager
        else:
            self.memory_manager = MemoryManager(session_memory=session_memory)

        # 注册学生
        if students:
            for profile in students:
                self.memory_manager.register_student(profile)

    def _build_system_prompt(self) -> str:
        """构建教师 system prompt.

        根据教学模式生成不同的系统提示。
        """
        topic = self.session_memory.topic
        context = self.memory_manager.session_memory.get_agent_context()
        teacher_context = self.memory_manager.teacher_memory.get_system_prompt_addition(topic=topic)

        mode_instructions = {
            "didactic": (
                "## 教学模式：灌输式\n"
                "- 以知识点讲解为主，连续讲授，不主动提问\n"
                "- 专注于清晰、系统地传授知识\n"
                "- 确保内容覆盖教学主题的所有关键知识点\n"
                "- 使用具体示例和类比帮助理解\n"
            ),
            "heuristic": (
                "## 教学模式：启发式\n"
                "- 结合案例教学，在讲授中穿插互动环节\n"
                "- 每讲授3-5个知识点后，提出一个 checkpoint 问题\n"
                "- 鼓励学生思考和回答\n"
                "- 根据学生回答情况调整讲解节奏\n"
            ),
            "discussion": (
                "## 教学模式：讨论式\n"
                "- 频繁提问，每1-2个知识点后引导一次讨论\n"
                "- 鼓励学生积极参与讨论和表达观点\n"
                "- 引导学生通过讨论深化理解\n"
                "- 对学生的观点给予反馈和补充\n"
            ),
        }

        mode_section = mode_instructions.get(
            self.teaching_mode, mode_instructions["didactic"]
        )

        return f"""你是教师 agent，正在教授"{topic}"相关内容。

## 基本信息
- 教学主题: {topic}
- 教学模式: {self.teaching_mode}

{mode_section}

{teacher_context}

## 重要提醒
1. 避免重复讲授已覆盖的知识点
2. 根据学生的参与度和理解程度调整教学节奏
3. 对于困惑的学生，提供更详细的解释
4. 每次讲授一个完整的知识点段，不要太长也不要太短
5. 使用通俗易懂的语言，适当使用类比和实例

{context}
"""

    def deliver_lecture(self) -> str:
        """生成讲授内容.

        Returns:
            讲授内容文本
        """
        system_prompt = self._build_system_prompt()
        user_prompt = (
            f"请继续讲授关于「{self.session_memory.topic}」的内容。"
        )

        content = self.llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._get_mode_temperature(),
        )

        # 通过 MemoryManager 处理消息
        message = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content=content,
            timestamp=datetime.now(),
        )
        self.memory_manager.process_message(message)

        return content

    def _get_mode_temperature(self) -> float:
        """根据教学模式获取合适的温度值.

        Returns:
            温度值
        """
        temperatures = {
            "didactic": 0.3,
            "heuristic": 0.5,
            "discussion": 0.7,
        }
        return temperatures.get(self.teaching_mode, 0.3)

    def is_content_complete(self) -> bool:
        """判断教学内容是否已完成.

        通过 LLM 判断已讲授的知识点是否覆盖了教学主题。

        Returns:
            True if teaching content is complete
        """
        topic = self.session_memory.topic
        covered = self.memory_manager.teacher_memory.covered_topics

        if not covered:
            return False

        prompt = (
            f"判断以下已讲授的知识点是否完整覆盖了「{topic}」这个教学主题的核心内容。\n\n"
            f"已讲授的知识点:\n" + "\n".join(f"- {kp}" for kp in covered)
            + "\n\n请只回答「完成」或「未完成」。"
        )

        response = self.llm.invoke(prompt, temperature=0.1)
        return "完成" in response
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentInit -v`
预期: 全部 4 个测试通过

- [ ] **步骤 5: 提交**

```bash
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat: add TeacherAgent with deliver_lecture() and mode-specific prompts"
```

---

### 任务 3: deliver_lecture() 与记忆系统集成

**文件:**
- 修改: `backend/tests/units/test_teacher_agent.py`

- [ ] **步骤 1: 编写失败测试**

```python
# 添加到 backend/tests/units/test_teacher_agent.py

class TestTeacherAgentLecture:
    """TeacherAgent 讲授功能测试."""

    def _make_agent(
        self, teaching_mode: str = "didactic", covered_topics: list[str] | None = None
    ) -> "TeacherAgent":
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

        llm_calls = []
        mock_llm = MagicMock(side_effect=lambda *args, **kwargs: llm_calls.append(kwargs))
        mock_llm.invoke.return_value = "这是关于变量的讲授内容。"

        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_deliver_lecture_calls_llm(self):
        """测试 deliver_lecture 调用 LLM."""
        agent = self._make_agent()

        agent.deliver_lecture()

        assert len(agent.llm.invoke.call_args_list) == 1

    def test_deliver_lecture_passes_system_prompt_with_context(self):
        """测试 deliver_lecture 传递包含记忆上下文的 system prompt."""
        agent = self._make_agent(covered_topics=["变量"])

        agent.deliver_lecture()

        call_kwargs = agent.llm.invoke.call_args[1]
        messages = call_kwargs["input"]
        system_msg = messages[0]["content"]

        assert "Python基础" in system_msg
        assert "变量" in system_msg  # 已讲授内容
        assert "灌输式" in system_msg  # 教学模式

    def test_deliver_lecture_uses_mode_temperature(self):
        """测试不同教学模式使用不同温度."""
        # 灌输式 = 0.3
        agent_didactic = self._make_agent(teaching_mode="didactic")
        agent_didactic.deliver_lecture()
        assert agent_didactic.llm.invoke.call_args[1].get("temperature") == 0.3

        # 启发式 = 0.5
        agent_heuristic = self._make_agent(teaching_mode="heuristic")
        agent_heuristic.deliver_lecture()
        assert agent_heuristic.llm.invoke.call_args[1].get("temperature") == 0.5

        # 讨论式 = 0.7
        agent_discussion = self._make_agent(teaching_mode="discussion")
        agent_discussion.deliver_lecture()
        assert agent_discussion.llm.invoke.call_args[1].get("temperature") == 0.7

    def test_deliver_lecture_updates_memory_manager(self):
        """测试 deliver_lecture 通过 MemoryManager 更新记忆."""
        from agents.memories import SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        agent = self._make_agent(session_memory=session_mem)

        # Mock LLM 返回包含知识点的内容
        agent.llm.invoke.return_value = "今天我们学习变量和数据类型。"

        # Mock extract_knowledge_fn
        agent.memory_manager.extract_knowledge_fn = lambda c: ["变量", "数据类型"]

        agent.deliver_lecture()

        assert "变量" in agent.memory_manager.teacher_memory.covered_topics
        assert "数据类型" in agent.memory_manager.teacher_memory.covered_topics
        assert len(session_mem.message_history) == 1
        assert session_mem.message_history[0].message_type == MessageType.LECTURE

    def test_deliver_lecture_heuristic_mode_includes_interaction(self):
        """测试启发式模式的 system prompt 包含互动指令."""
        agent = self._make_agent(teaching_mode="heuristic")

        agent.deliver_lecture()

        call_kwargs = agent.llm.invoke.call_args[1]
        system_msg = call_kwargs["input"][0]["content"]

        assert "checkpoint" in system_msg.lower() or "提问" in system_msg.lower()

    def test_deliver_lecture_discussion_mode_includes_discussion(self):
        """测试讨论式模式的 system prompt 包含讨论指令."""
        agent = self._make_agent(teaching_mode="discussion")

        agent.deliver_lecture()

        call_kwargs = agent.llm.invoke.call_args[1]
        system_msg = call_kwargs["input"][0]["content"]

        assert "讨论" in system_msg.lower()
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentLecture -v`
预期: FAIL（各种断言错误，取决于实现状态）

- [ ] **步骤 3: 验证所有测试通过**

运行: `cd backend && python -m pytest tests/units/test_teacher_agent.py -v`
预期: 全部测试通过

- [ ] **步骤 4: 提交**

```bash
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "test: add deliver_lecture() tests with mode-specific behavior verification"
```

---

### 任务 4: is_content_complete() 方法

**文件:**
- 修改: `backend/tests/units/test_teacher_agent.py`

- [ ] **步骤 1: 编写失败测试**

```python
# 添加到 backend/tests/units/test_teacher_agent.py

class TestTeacherAgentContentComplete:
    """TeacherAgent 内容完成判断测试."""

    def _make_agent(self, covered_topics: list[str] | None = None) -> "TeacherAgent":
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础变量")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)

        llm_calls = []
        mock_llm = MagicMock(side_effect=lambda *args, **kwargs: llm_calls.append(kwargs))
        mock_llm.invoke.return_value = "未完成"

        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            memory_manager=mm,
        )

    def test_content_complete_no_topics_returns_false(self):
        """测试无已讲授知识点时返回 False."""
        agent = self._make_agent()

        assert agent.is_content_complete() is False

    def test_content_complete_with_partial_topics(self):
        """测试部分知识点时返回 False."""
        agent = self._make_agent(covered_topics=["变量"])

        assert agent.is_content_complete() is False

    def test_content_complete_with_all_topics_returns_true(self):
        """测试知识点完整覆盖时返回 True."""
        agent = self._make_agent(covered_topics=["变量", "数据类型", "条件语句", "循环"])

        # Mock LLM 返回 "完成"
        agent.llm.invoke.return_value = "完成"

        assert agent.is_content_complete() is True

    def test_content_complete_sends_topic_and_topics(self):
        """测试 LLM 调用包含教学主题和知识点列表."""
        agent = self._make_agent(covered_topics=["变量"])

        agent.is_content_complete()

        call_kwargs = agent.llm.invoke.call_args[1]
        prompt = call_kwargs.get("input", "")

        assert "Python基础变量" in prompt
        assert "变量" in prompt
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentContentComplete -v`
预期: FAIL（断言错误）

- [ ] **步骤 3: 验证测试通过**

运行: `cd backend && python -m pytest tests/units/test_teacher_agent.py::TestTeacherAgentContentComplete -v`
预期: 全部测试通过

- [ ] **步骤 4: 提交**

```bash
git add backend/agents/teacher_agent.py backend/tests/units/test_teacher_agent.py
git commit -m "feat: add is_content_complete() with LLM-based content coverage judgment"
```

---

### 任务 5: 确保 .env 文件加载

**文件:**
- 修改: `backend/main.py`（确保启动时加载 .env）

- [ ] **步骤 1: 确认 main.py 中已加载 .env**

阅读 `backend/main.py`，确认已包含 `dotenv.load_dotenv()` 或等效逻辑。如果没有，添加:

```python
from dotenv import load_dotenv

load_dotenv()  # 在应用启动前调用
```

- [ ] **步骤 2: 运行所有测试验证无回归**

运行: `cd backend && python -m pytest tests/ -q`
预期: 全部测试通过

- [ ] **步骤 3: 提交（如有改动）**

```bash
git add backend/main.py
git commit -m "chore: ensure .env is loaded at app startup"
```

---

### 任务 6: 运行所有测试和代码检查

- [ ] **步骤 1: 运行所有测试**

运行: `cd backend && python -m pytest tests/ -q`
预期: 全部测试通过

- [ ] **步骤 2: 运行 ruff 检查**

运行: `cd backend && ruff check agents/ core/llm_client.py tests/`
预期: 所有检查通过

- [ ] **步骤 3: 如需修复 lint 问题则提交**

```bash
git add -A
git commit -m "chore: fix lint issues"
```

---

## 自检清单

**1. 需求覆盖:**
- [x] LangChain 基础集成（硅基流动 API, Qwen2.5-7B-Instruct） → 任务 1
- [x] MemoryAwareTeacherAgent 基础结构（init, LLM, MemoryManager） → 任务 2
- [x] deliver_lecture() 方法 → 任务 3
- [x] 根据 teaching_mode 调整讲授风格 → 任务 3（模式特定 prompt 和温度）
- [x] 讲授内容与教学主题相关 → 任务 3（system prompt 包含主题）
- [x] is_content_complete() → 任务 4
- [x] 能连接 LLM API → 任务 1（LLMClient 带 API key）
- [x] 能输出讲授内容（lecture） → 任务 3（deliver_lecture 返回 LLM 输出）
- [x] 验证：调用 agent，查看输出内容 → 任务 3 测试

**2. 占位符扫描:**
- [x] 无 TBD、TODO 或 "implement later"
- [x] 所有代码块包含完整实现
- [x] 所有命令包含预期输出

**3. 类型一致性:**
- [x] `MessageType.LECTURE` 在 deliver_lecture 测试和实现中一致使用
- [x] `teaching_mode` 参数始终为 `str` 类型
- [x] LLM 客户端 `invoke()` 返回 `str` 类型
- [x] `deliver_lecture()` 返回 `str`
- [x] `is_content_complete()` 返回 `bool`
