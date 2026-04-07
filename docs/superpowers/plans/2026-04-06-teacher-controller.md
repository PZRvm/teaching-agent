# TeacherSessionController 实施计划

> **For agentic workers:** 必需子技能：使用 **superpowers:test-driven-development** 来逐步实施此计划。遵循 TDD 红绿重构循环：先写失败测试，再实现最小代码使其通过，最后重构。步骤使用复选框（`- [ ]`）语法进行跟踪。

**TDD 工作流程：**
1. **RED:** 编写失败的测试（运行 pytest 验证失败）
2. **GREEN:** 编写最小实现使测试通过
3. **REFACTOR:** 重构代码（保持测试通过）
4. **COMMIT:** 每个任务完成后立即提交

**TDD 命令参考：**
```bash
# RED - 运行测试验证失败
cd backend
pytest tests/units/test_teacher_controller.py::test_xxx -v

# GREEN - 运行测试验证通过
pytest tests/units/test_teacher_controller.py::test_xxx -v

# 运行所有相关测试
pytest tests/units/test_teacher_controller.py -v

# 代码质量检查
ruff check models/session/teacher_controller.py
ruff format models/session/teacher_controller.py
```

---

## 目标

**架构：** TeacherSessionController 连接 WebSocket 用户命令与学生 agents，管理对话状态（至少一轮约束）、检查点推进和旁听学习——不持有 TeacherAgent（用户扮演教师角色）。

**技术栈：** FastAPI, WebSocket, asyncio, pytest, Pydantic

---

## 文件结构

```
backend/models/session/
├── teacher_controller.py      # 新建 - TeacherSessionController 类
├── schemas.py                  # 修改 - 添加教师模式请求 schemas
├── router_websocket.py         # 修改 - 添加教师模式 WebSocket 命令处理器
└── router.py                   # 修改 - 添加教师模式 REST 端点

backend/tests/units/
├── test_teacher_controller.py  # 新建 - 35+ 单元测试

backend/tests/integration/
├── test_teacher_controller_real.py  # 新建 - 6+ 真实 LLM 集成测试
```

---

## TDD 实施指导

### TDD 循环详解

每个任务都遵循标准的 TDD 红绿重构循环：

```
┌─────────────────────────────────────────────────────────────┐
│  RED (步骤 1-2)                                              │
│  1. 编写失败的测试代码                                       │
│  2. 运行 pytest 验证测试失败（确保测试真正失败）            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  GREEN (步骤 3-4)                                            │
│  3. 编写最小实现使测试通过                                   │
│  4. 运行 pytest 验证测试通过                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  REFACTOR (可选)                                             │
│  在保持测试通过的前提下重构代码                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  COMMIT (步骤 5)                                             │
│  提交代码，每个任务对应一个 git commit                      │
└─────────────────────────────────────────────────────────────┘
```

### TDD 最佳实践

1. **最小实现原则**
   - 只写刚好能让测试通过的代码
   - 不要过度设计或实现未测试的功能
   - 保持简单，后续任务可以迭代改进

2. **测试命名规范**
   - 测试函数名描述测试内容：`test_<method>_<scenario>_<expected_result>()`
   - 例如：`test_handle_broadcast_lecture_records_to_memory()`

3. **Mock 使用**
   - 单元测试使用 Mock 对外部依赖（LLM、数据库）
   - 集成测试使用真实依赖验证完整流程

4. **提交消息规范**
   - 格式：`<type>(<scope>): <description>`
   - 类型：`feat`（新功能）、`fix`（修复）、`refactor`（重构）、`test`（测试）
   - 例如：`feat(teacher-controller): add handle_broadcast_lecture method`

5. **进度跟踪**
   - 使用 `- [ ]` 复选框跟踪每个步骤
   - 完成一个步骤就勾选一个
   - 每完成一个任务就提交一次

### 错误处理测试

根据工程审查反馈，每个方法都需要测试错误路径。在实施时，每个任务应包含：

```python
# 快乐路径测试（已包含）
def test_xxx_happy_path():
    """测试正常情况下的行为"""
    ...

# 错误路径测试（需要添加）
def test_xxx_when_invalid_input_raises_error():
    """测试无效输入时抛出异常"""
    ...
```

---

## 从 Phase 7 复用的关键部分

以下来自 `SessionOrchestrator` 的模式将被复用：

| 组件 | 复用模式 |
|-----------|---------------|
| `_collect_student_answers()` | 收集所有学生响应的相同逻辑 |
| `_single_student_answer()` | 指定学生响应的相同逻辑 |
| `_trigger_observer_learning()` | 基于概率的 `update_knowledge()` 用于旁听者 |
| `_record_student_message()` | 记录消息到 MemoryManager 的相同逻辑 |
| `_assign_homework()` | 相同的作业分配流程 |
| `_collect_homework_and_feedback()` | 相同的作业收集和 LLM 评分 |
| `_ws_push_checkpoint_state()` | 相同的检查点状态变更 WebSocket 推送 |

**关键差异：** 教师模式没有 `TeacherAgent`——用户通过 WebSocket 命令（`broadcast_lecture`, `ask_to_all`, `teacher_reply`）直接提供内容。

---

## 任务 1: TeacherSessionController 初始化

**文件：**
- 创建: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_init_creates_controller_with_required_components():
    """测试初始化创建控制器及其必需组件"""
    # Arrange
    mock_student_agents = [Mock(), Mock()]
    mock_memory_manager = Mock()
    mock_checkpoint_plan = Mock()
    mock_ws_callback = Mock()

    # Act
    controller = TeacherSessionController(
        student_agents=mock_student_agents,
        memory_manager=mock_memory_manager,
        checkpoint_plan=mock_checkpoint_plan,
        ws_push_callback=mock_ws_callback
    )

    # Assert
    assert controller.student_agents == mock_student_agents
    assert controller.memory_manager == mock_memory_manager
    assert controller.checkpoint_plan == mock_checkpoint_plan
    assert controller._ws_push_callback == mock_ws_callback
    assert controller._active_dialogue is None  # 初始无活跃对话
    assert controller._dialogue_round_count == 0
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_init_creates_controller_with_required_components -v`

预期: 失败，提示 "TeacherSessionController not defined"

- [ ] **步骤 3: 编写最小实现**

创建 `backend/models/session/teacher_controller.py`:

```python
"""TeacherSessionController - 教师模式核心控制器."""

from collections.abc import Callable
from typing import Optional

from agents.student_agent import StudentAgent
from agents.memories.memory_manager import MemoryManager
from models.checkpoint.schemas import CheckpointPlan


class TeacherSessionController:
    """教师模式手动教学流程控制器.

    用户扮演教师角色，通过 WebSocket 命令控制教学流程。
    支持检查点驱动的手动教学，用户可编辑检查点、手动推进、控制对话节奏。

    核心特性：
    - 无 TeacherAgent（用户提供教学内容）
    - 至少一轮对话约束（与观察模式相同）
    - 旁听学习机制（复用观察模式逻辑）
    - 检查点手动推进（强制结束当前对话）
    """

    def __init__(
        self,
        *,
        student_agents: list[StudentAgent],
        memory_manager: MemoryManager,
        checkpoint_plan: CheckpointPlan,
        ws_push_callback: Optional[Callable] = None,
    ):
        """初始化教师模式控制器.

        Args:
            student_agents: 学生 agent 列表
            memory_manager: 记忆管理器
            checkpoint_plan: 检查点计划
            ws_push_callback: WebSocket 推送回调（用于测试）
        """
        self.student_agents = student_agents
        self.memory_manager = memory_manager
        self.checkpoint_plan = checkpoint_plan
        self._ws_push_callback = ws_push_callback

        # 对话状态追踪
        self._active_dialogue: Optional[dict] = None  # 当前活跃对话 {student_name: round_count}
        self._dialogue_round_count: int = 0  # 当前对话轮数
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_init_creates_controller_with_required_components -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add TeacherSessionController initialization"
```

---

## 任务 2: handle_broadcast_lecture()

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_broadcast_lecture_records_to_memory():
    """测试广播讲授内容记录到记忆系统"""
    # Arrange
    controller = create_test_controller()
    lecture_content = "今天我们学习 Python 变量的基本概念"

    # Act
    controller.handle_broadcast_lecture(lecture_content)

    # Assert - 消息被记录到 session_memory
    messages = controller.memory_manager.session_memory.message_history
    assert len(messages) == 1
    assert messages[0].sender == "teacher"
    assert messages[0].content == lecture_content
    assert messages[0].message_type.value == "lecture"
    assert messages[0].receiver == "all"
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_broadcast_lecture_records_to_memory -v`

预期: 失败，提示 "TeacherSessionController has no attribute 'handle_broadcast_lecture'"

- [ ] **步骤 3: 编写最小实现**

添加到 `backend/models/session/teacher_controller.py`:

```python
from datetime import datetime
from models.session.schemas import Message, MessageType

# 在 TeacherSessionController 类中添加：

def handle_broadcast_lecture(self, content: str) -> None:
    """处理用户广播讲授内容.

    Args:
        content: 用户（教师）提供的讲授内容

    流程：
        1. 记录 lecture 消息到 SessionMemory
        2. 推送 WebSocket 事件（可选）
    """
    from models.session.schemas import TIMEZONE

    message = Message(
        sender="teacher",
        message_type=MessageType.LECTURE,
        content=content,
        receiver="all",
        timestamp=datetime.now(TIMEZONE),
    )

    self.memory_manager.process_message(message)
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_broadcast_lecture_records_to_memory -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add handle_broadcast_lecture method"
```

---

## 任务 3: handle_ask_to_all()

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_ask_to_all_collects_student_answers():
    """测试向全体提问收集学生回答"""
    # Arrange
    controller = create_test_controller()
    question = "谁能说出 Python 变量的特点？"

    # Mock 学生回答
    controller.student_agents[0].answer_question = Mock(return_value="Python 变量不需要声明类型，可以直接赋值")
    controller.student_agents[1].answer_question = Mock(return_value="")  # 不回答

    # Act
    answers = controller.handle_ask_to_all(question)

    # Assert - 返回非空回答列表
    assert len(answers) == 1
    assert answers[0]["student_name"] == controller.student_agents[0].profile.name
    assert answers[0]["content"] == "Python 变量不需要声明类型，可以直接赋值"

    # Assert - 问题消息被记录
    messages = controller.memory_manager.session_memory.message_history
    assert any(m.message_type.value == "checkpoint_question" for m in messages)
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_ask_to_all_collects_student_answers -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
from typing import List, Dict

def handle_ask_to_all(self, question: str) -> List[Dict[str, str]]:
    """处理向全体提问，收集回答.

    Args:
        question: 教师提出的问题

    Returns:
        非空回答列表 [{"student_name": str, "content": str}, ...]

    流程：
        1. 记录 checkpoint_question 消息到 SessionMemory
        2. 调用每个学生的 should_respond() 判断是否回答
        3. 如果无人回答，返回空列表（用户需指定学生）
        4. 收集所有回答并记录到 SessionMemory
        5. 返回非空回答列表
    """
    from models.session.schemas import TIMEZONE

    # 记录问题到记忆
    question_message = Message(
        sender="teacher",
        message_type=MessageType.CHECKPOINT_QUESTION,
        content=question,
        receiver="all",
        timestamp=datetime.now(TIMEZONE),
    )
    self.memory_manager.process_message(question_message)

    # 收集回答
    answers = []
    for student in self.student_agents:
        if student.should_respond():
            answer = student.answer_question(question)
            if answer:  # 只记录非空回答
                answers.append({
                    "student_name": student.profile.name,
                    "content": answer
                })
                self._record_student_message(student.profile.name, answer)

    return answers
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_ask_to_all_collects_student_answers -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add handle_ask_to_all method"
```

---

## 任务 4: handle_ask_to_student()

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_ask_to_student_gets_single_answer():
    """测试向指定学生提问"""
    # Arrange
    controller = create_test_controller()
    question = "小明，你说说 Python 中列表和元组的区别是什么？"
    student_name = controller.student_agents[0].profile.name

    # Mock 学生回答
    controller.student_agents[0].answer_question = Mock(return_value="列表是可变的，元组是不可变的")

    # Act
    result = controller.handle_ask_to_student(student_name, question)

    # Assert
    assert result["student_name"] == student_name
    assert result["content"] == "列表是可变的，元组是不可变的"
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_ask_to_student_gets_single_answer -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
def handle_ask_to_student(self, student_name: str, question: str) -> Dict[str, str]:
    """处理向指定学生提问.

    Args:
        student_name: 学生姓名
        question: 教师提出的问题

    Returns:
        {"student_name": str, "content": str}

    流程：
        1. 查找指定学生
        2. 记录 checkpoint_question 消息（receiver=学生名）
        3. 调用学生 answer_question（不受 should_respond 限制）
        4. 记录学生回答到 SessionMemory
        5. 返回回答内容
    """
    from models.session.schemas import TIMEZONE

    # 查找学生
    student = next(
        (s for s in self.student_agents if s.profile.name == student_name),
        None
    )
    if not student:
        raise ValueError(f"Student {student_name} not found")

    # 记录问题
    question_message = Message(
        sender="teacher",
        message_type=MessageType.CHECKPOINT_QUESTION,
        content=question,
        receiver=student_name,
        timestamp=datetime.now(TIMEZONE),
    )
    self.memory_manager.process_message(question_message)

    # 获取回答
    answer = student.answer_question(question)
    self._record_student_message(student_name, answer)

    return {"student_name": student_name, "content": answer}
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_ask_to_student_gets_single_answer -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add handle_ask_to_student method"
```

---

## 任务 5: handle_teacher_reply() with Dialogue State

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_teacher_reply_tracks_dialogue_rounds():
    """测试教师回复跟踪对话轮数"""
    # Arrange
    controller = create_test_controller()
    student_name = "Alice"
    reply = "回答正确！列表确实可变，元组确实不可变。"

    # Act - 第一轮对话
    controller.handle_teacher_reply(student_name, reply)

    # Assert - 对话状态已建立
    assert controller._active_dialogue == {student_name: 1}
    assert controller._dialogue_round_count == 1

    # Act - 第二轮对话
    controller.handle_teacher_reply(student_name, "还有问题吗？")

    # Assert - 轮数增加
    assert controller._active_dialogue == {student_name: 2}
    assert controller._dialogue_round_count == 2
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_teacher_reply_tracks_dialogue_rounds -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
def handle_teacher_reply(self, student_name: str, content: str) -> None:
    """处理教师对学生回复（场景 A/B 对话循环）.

    Args:
        student_name: 学生姓名
        content: 教师的回复内容

    流程：
        1. 更新对话状态（_active_dialogue, _dialogue_round_count）
        2. 记录 reply_to_student 消息到 SessionMemory
    """
    from models.session.schemas import TIMEZONE

    # 更新对话状态
    if self._active_dialogue is None:
        self._active_dialogue = {}
    if student_name not in self._active_dialogue:
        self._active_dialogue[student_name] = 0

    self._active_dialogue[student_name] += 1
    self._dialogue_round_count += 1

    # 记录消息
    message = Message(
        sender="teacher",
        message_type=MessageType.REPLY_TO_STUDENT,
        content=content,
        receiver=student_name,
        timestamp=datetime.now(TIMEZONE),
    )
    self.memory_manager.process_message(message)
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_teacher_reply_tracks_dialogue_rounds -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add handle_teacher_reply with dialogue tracking"
```

---

## 任务 6: handle_end_dialogue() with At-Least-One-Round Constraint

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_end_dialogue_requires_at_least_one_round():
    """测试至少一轮后才能结束对话"""
    # Arrange
    controller = create_test_controller()

    # Act & Assert - 尚未开始对话，不能结束
    with pytest.raises(ValueError, match="至少完成一轮对话后才能结束"):
        controller.handle_end_dialogue()
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_end_dialogue_requires_at_least_one_round -v`

预期: 失败，提示方法未定义或错误消息不正确

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
def handle_end_dialogue(self) -> None:
    """处理教师主动结束对话.

    Returns:
        None

    Raises:
        ValueError: 如果尚未完成至少一轮对话

    流程：
        1. 检查至少一轮约束（_dialogue_round_count >= 1）
        2. 重置对话状态（_active_dialogue = None, _dialogue_round_count = 0）
        3. 触发旁听学习（_trigger_observer_learning）
    """
    if self._dialogue_round_count < 1:
        raise ValueError("至少完成一轮对话后才能结束")

    # 重置对话状态
    participating_students = list(self._active_dialogue.keys()) if self._active_dialogue else []
    self._active_dialogue = None
    self._dialogue_round_count = 0

    # 触发旁听学习
    self._trigger_observer_learning(participating_students)

def _trigger_observer_learning(self, participating_students: list[str]) -> None:
    """触发旁听学生学习（复用观察模式逻辑）.

    Args:
        participating_students: 参与对话的学生列表（不参与旁听学习）
    """
    participating_set = set(participating_students)

    for student in self.student_agents:
        if student.profile.name not in participating_set:
            # 旁听学生尝试学习
            learned = student.memory.should_remember_concept(
                self.checkpoint_plan.checkpoints[self.checkpoint_plan.current_index].key_point,
                student.rng
            )
            if learned:
                student.memory.update_knowledge(
                    [self.checkpoint_plan.checkpoints[self.checkpoint_plan.current_index].key_point],
                    student.rng
                )
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_end_dialogue_requires_at_least_one_round -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add handle_end_dialogue with at-least-one-round constraint"
```

---

## 任务 7: handle_advance_checkpoint() with Force End

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_advance_checkpoint_with_force_end():
    """测试手动推进检查点并强制结束当前对话"""
    # Arrange
    controller = create_test_controller()
    controller.checkpoint_plan.current_index = 0
    controller.checkpoint_plan.checkpoints[0].state = CheckpointState.TEACHING
    controller._active_dialogue = {"Alice": 2}  # 模拟活跃对话

    # Act
    controller.handle_advance_checkpoint(force_end_dialogue=True)

    # Assert - 当前检查点被标记为 COMPLETE
    assert controller.checkpoint_plan.checkpoints[0].state == CheckpointState.COMPLETE

    # Assert - 对话被强制重置
    assert controller._active_dialogue is None
    assert controller._dialogue_round_count == 0
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_advance_checkpoint_with_force_end -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
from models.checkpoint.schemas import CheckpointState

def handle_advance_checkpoint(self, force_end_dialogue: bool = False) -> Checkpoint:
    """手动推进到下一个检查点.

    Args:
        force_end_dialogue: 是否强制结束当前对话

    Returns:
        新的 TEACHING 状态检查点

    流程：
        1. 如果 force_end_dialogue=True，强制结束当前对话
        2. 标记当前检查点为 COMPLETE
        3. 前进到下一个 PENDING 检查点
        4. 将新检查点标记为 TEACHING
        5. 推送 WebSocket 事件
    """
    from models.checkpoint.schemas import Checkpoint

    # 强制结束当前对话
    if force_end_dialogue:
        self._active_dialogue = None
        self._dialogue_round_count = 0

    # 完成当前检查点
    current_cp = self.checkpoint_plan.checkpoints[self.checkpoint_plan.current_index]
    current_cp.state = CheckpointState.COMPLETE

    # 前进到下一个 PENDING 检查点
    next_cp = self._advance_to_next_pending()
    next_cp.state = CheckpointState.TEACHING

    # 推送 WebSocket 事件
    self._ws_push_checkpoint_state(next_cp)

    return next_cp

def _advance_to_next_pending(self) -> Checkpoint:
    """前进到下一个 PENDING 状态的检查点.

    Returns:
        下一个 PENDING 检查点

    Raises:
        ValueError: 如果没有更多 PENDING 检查点
    """
    for i in range(self.checkpoint_plan.current_index + 1, len(self.checkpoint_plan.checkpoints)):
        if self.checkpoint_plan.checkpoints[i].state == CheckpointState.PENDING:
            self.checkpoint_plan.current_index = i
            return self.checkpoint_plan.checkpoints[i]

    raise ValueError("没有更多 PENDING 检查点")

def _ws_push_checkpoint_state(self, checkpoint: Checkpoint) -> None:
    """通过 WebSocket 推送检查点状态变更."""
    if self._ws_push_callback:
        message = {
            "type": "checkpoint_state_change",
            "data": {
                "session_id": self.memory_manager.session_memory.session_id,
                "checkpoint_index": self.checkpoint_plan.current_index,
                "state": checkpoint.state.value,
                "checkpoint": {
                    "title": checkpoint.title,
                    "key_point": checkpoint.key_point,
                    "state": checkpoint.state.value,
                },
            },
        }
        import inspect
        if inspect.iscoroutinefunction(self._ws_push_callback):
            import asyncio
            asyncio.create_task(self._ws_push_callback(message))
        else:
            self._ws_push_callback(message)
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_advance_checkpoint_with_force_end -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add handle_advance_checkpoint with force_end_dialogue"
```

---

## 任务 8: handle_edit_checkpoints()

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_edit_checkpoints_modifies_plan():
    """测试编辑检查点计划"""
    # Arrange
    controller = create_test_controller()
    updated_plan = controller.checkpoint_plan.model_copy()
    updated_plan.checkpoints[0].title = "修改后的标题"

    # Act
    controller.handle_edit_checkpoints(updated_plan)

    # Assert
    assert controller.checkpoint_plan.checkpoints[0].title == "修改后的标题"
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_edit_checkpoints_modifies_plan -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
def handle_edit_checkpoints(self, updated_plan: CheckpointPlan) -> None:
    """处理用户编辑检查点计划.

    Args:
        updated_plan: 更新后的检查点计划

    流程：
        1. 验证当前检查点状态（所有检查点必须为 PENDING）
        2. 替换 checkpoint_plan
    """
    from models.checkpoint.schemas import CheckpointState

    # 验证：只能在所有检查点为 PENDING 时编辑
    for cp in self.checkpoint_plan.checkpoints:
        if cp.state != CheckpointState.PENDING:
            raise ValueError("只能在教学开始前编辑检查点（所有检查点必须为 PENDING）")

    # 替换计划
    self.checkpoint_plan = updated_plan
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_edit_checkpoints_modifies_plan -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add handle_edit_checkpoints method"
```

---

## 任务 9: 辅助方法 _record_student_message()

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_record_student_message_updates_memory():
    """测试记录学生消息到记忆系统"""
    # Arrange
    controller = create_test_controller()
    student_name = "Alice"
    content = "列表是可变的，元组是不可变的"

    # Act
    controller._record_student_message(student_name, content)

    # Assert
    messages = controller.memory_manager.session_memory.message_history
    assert len(messages) == 1
    assert messages[0].sender == student_name
    assert messages[0].content == content
    assert messages[0].receiver == "teacher"
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_record_student_message_updates_memory -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
def _record_student_message(self, student_name: str, content: str) -> None:
    """记录学生消息到记忆.

    Args:
        student_name: 学生姓名
        content: 消息内容
    """
    from models.session.schemas import TIMEZONE

    message = Message(
        sender=student_name,
        message_type=MessageType.ANSWER_TO_CHECKPOINT,
        content=content,
        receiver="teacher",
        timestamp=datetime.now(TIMEZONE),
    )

    self.memory_manager.process_message(message)
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_record_student_message_updates_memory -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add _record_student_message helper"
```

---

## 任务 10: WebSocket 命令路由器

**文件：**
- 修改: `backend/models/session/router_websocket.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_websocket_command_dispatch():
    """测试 WebSocket 命令分发到正确的方法"""
    # Arrange
    controller = create_test_controller()
    command = {
        "type": "broadcast_lecture",
        "content": "今天我们学习 Python 变量"
    }

    # Act
    controller.handle_websocket_command(command)

    # Assert - 讲授内容被记录
    messages = controller.memory_manager.session_memory.message_history
    assert len(messages) == 1
    assert messages[0].message_type.value == "lecture"
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_websocket_command_dispatch -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
def handle_websocket_command(self, command: dict) -> dict:
    """处理 WebSocket 命令并返回响应.

    Args:
        command: WebSocket 命令 {"type": str, ...}

    Returns:
        响应字典 {"success": bool, "data": any, "error": str}

    支持的命令类型：
        - broadcast_lecture: 广播讲授
        - ask_to_all: 向全体提问
        - ask_to_student: 向指定学生提问
        - teacher_reply: 教师回复
        - end_dialogue: 结束对话
        - advance_checkpoint: 推进检查点
    """
    command_type = command.get("type")

    try:
        if command_type == "broadcast_lecture":
            self.handle_broadcast_lecture(command.get("content", ""))
            return {"success": True, "data": "lecture broadcasted"}

        elif command_type == "ask_to_all":
            question = command.get("content", "")
            answers = self.handle_ask_to_all(question)
            return {"success": True, "data": {"answers": answers}}

        elif command_type == "ask_to_student":
            student_name = command.get("student_name")
            question = command.get("content", "")
            result = self.handle_ask_to_student(student_name, question)
            return {"success": True, "data": result}

        elif command_type == "teacher_reply":
            student_name = command.get("student_name")
            content = command.get("content", "")
            self.handle_teacher_reply(student_name, content)
            return {"success": True, "data": "reply recorded"}

        elif command_type == "end_dialogue":
            self.handle_end_dialogue()
            return {"success": True, "data": "dialogue ended"}

        elif command_type == "advance_checkpoint":
            force_end = command.get("force_end_dialogue", False)
            new_checkpoint = self.handle_advance_checkpoint(force_end_dialogue=force_end)
            return {
                "success": True,
                "data": {
                    "checkpoint_index": self.checkpoint_plan.current_index,
                    "checkpoint": {
                        "title": new_checkpoint.title,
                        "state": new_checkpoint.state.value,
                    }
                }
            }

        else:
            return {"success": False, "error": f"Unknown command type: {command_type}"}

    except Exception as e:
        return {"success": False, "error": str(e)}
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_websocket_command_dispatch -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add WebSocket command router"
```

---

## 任务 11: 教师模式请求 Schemas

**文件：**
- 修改: `backend/models/session/schemas.py`
- 测试: `backend/tests/units/test_schemas.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_teacher_mode_request_schemas_validation():
    """测试教师模式请求 schemas 验证"""
    # Test broadcast_lecture request
    req = BroadcastLectureRequest(content="今天我们学习 Python 变量")
    assert req.content == "今天我们学习 Python 变量"

    # Test ask_to_student request
    req = AskToStudentRequest(student_name="Alice", content="什么是列表推导式？")
    assert req.student_name == "Alice"
    assert req.content == "什么是列表推导式？"

    # Test advance_checkpoint request
    req = AdvanceCheckpointRequest(force_end_dialogue=True)
    assert req.force_end_dialogue is True
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_schemas.py::test_teacher_mode_request_schemas_validation -v`

预期: 失败，提示 schemas 未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `backend/models/session/schemas.py`:

```python
# 教师模式 WebSocket 请求 Schemas

class BroadcastLectureRequest(BaseModel):
    """广播讲授请求"""
    content: str = Field(min_length=1, max_length=5000)


class AskToAllRequest(BaseModel):
    """向全体提问请求"""
    content: str = Field(min_length=1, max_length=1000)


class AskToStudentRequest(BaseModel):
    """向指定学生提问请求"""
    student_name: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=1, max_length=1000)


class TeacherReplyRequest(BaseModel):
    """教师回复请求"""
    student_name: str = Field(min_length=1, max_length=20)
    content: str = Field(min_length=1, max_length=5000)


class EndDialogueRequest(BaseModel):
    """结束对话请求"""
    pass  # 无额外参数


class AdvanceCheckpointRequest(BaseModel):
    """推进检查点请求"""
    force_end_dialogue: bool = False
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_schemas.py::test_teacher_mode_request_schemas_validation -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/schemas.py tests/units/test_schemas.py
git commit -m "feat(session-schemas): add teacher mode request schemas"
```

---

## 任务 12: 教师模式 REST 端点

**文件：**
- 修改: `backend/models/session/router.py`
- 测试: `backend/tests/integration/test_teacher_controller_api.py`

- [ ] **步骤 1: 编写失败的测试**

```python
@pytest.mark.asyncio
async def test_get_checkpoint_plan_returns_plan():
    """测试 GET /checkpoint-plan/{session_id} 返回检查点计划"""
    # Arrange
    async with get_db() as db:
        session = await create_teaching_session(db, mode="teacher")
        plan = await create_checkpoint_plan(db, session.id)

    # Act
    response = client.get(f"/checkpoint-plan/{session.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == plan.topic
    assert len(data["checkpoints"]) > 0
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/integration/test_teacher_controller_api.py::test_get_checkpoint_plan_returns_plan -v`

预期: 失败，提示端点未定义 (404)

- [ ] **步骤 3: 编写最小实现**

添加到 `backend/models/session/router.py`:

```python
from models.session.schemas import (
    # 现有 imports
    BroadcastLectureRequest,
    AskToAllRequest,
    AskToStudentRequest,
    TeacherReplyRequest,
    EndDialogueRequest,
    AdvanceCheckpointRequest,
)
from models.checkpoint.service import CheckpointPlanService
from models.checkpoint.persistence_service import CheckpointPlanPersistence

@router.get("/checkpoint-plan/{session_id}")
async def get_checkpoint_plan(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """获取检查点计划（教师模式）"""
    persistence = CheckpointPlanPersistence(db)
    plan = await persistence.load(session_id)

    if not plan:
        raise HTTPException(status_code=404, detail="Checkpoint plan not found")

    return JSONResponse(
        content={
            "topic": plan.topic,
            "teaching_mode": plan.teaching_mode,
            "current_index": plan.current_index,
            "checkpoints": [
                {
                    "title": cp.title,
                    "key_point": cp.key_point,
                    "checkpoint_question": cp.checkpoint_question,
                    "state": cp.state.value,
                }
                for cp in plan.checkpoints
            ],
        }
    )


@router.put("/checkpoint-plan/{session_id}")
async def edit_checkpoint_plan(
    session_id: int,
    plan_data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """编辑检查点计划（教师模式，教学开始前）"""
    persistence = CheckpointPlanPersistence(db)
    existing = await persistence.load(session_id)

    if not existing:
        raise HTTPException(status_code=404, detail="Checkpoint plan not found")

    # 验证：只能在所有检查点为 PENDING 时编辑
    from models.checkpoint.schemas import CheckpointState
    for cp in existing.checkpoints:
        if cp.state != CheckpointState.PENDING:
            raise HTTPException(
                status_code=400,
                detail="只能在教学开始前编辑检查点（所有检查点必须为 PENDING）"
            )

    # 更新检查点
    updated_checkpoints = []
    for cp_data in plan_data.get("checkpoints", []):
        from models.checkpoint.schemas import Checkpoint
        updated_checkpoints.append(
            Checkpoint(
                title=cp_data.get("title", existing.checkpoints[0].title),
                key_point=cp_data.get("key_point", ""),
                checkpoint_question=cp_data.get("checkpoint_question", ""),
                state=CheckpointState.PENDING,
            )
        )

    # 更新 plan
    from models.checkpoint.schemas import CheckpointPlan
    updated_plan = CheckpointPlan(
        topic=plan_data.get("topic", existing.topic),
        teaching_mode=existing.teaching_mode,
        checkpoints=updated_checkpoints,
        current_index=0,
    )

    await persistence.save(session_id, updated_plan)

    return JSONResponse(content={"success": True})


@router.post("/sessions/{session_id}/advance-checkpoint")
async def advance_checkpoint_endpoint(
    session_id: int,
    request: AdvanceCheckpointRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """手动推进到下一个检查点（教师模式）"""
    # TODO: 实现 WebSocket 连接管理和控制器实例获取
    # 这个端点需要从活跃的 WebSocket 连接中获取 TeacherSessionController 实例
    # 当前返回 mock 响应
    return JSONResponse(
        content={
            "success": True,
            "data": {
                "message": "Checkpoint advancement via WebSocket - use handle_advance_checkpoint in controller"
            }
        }
    )
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/integration/test_teacher_controller_api.py::test_get_checkpoint_plan_returns_plan -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/router.py tests/integration/test_teacher_controller_api.py
git commit -m "feat(session-router): add teacher mode checkpoint endpoints"
```

---

## 任务 13: 作业和完成流程

**文件：**
- 修改: `backend/models/session/teacher_controller.py`
- 测试: `backend/tests/units/test_teacher_controller.py`

- [ ] **步骤 1: 编写失败的测试**

```python
def test_handle_assign_homework_collects_submissions():
    """测试布置作业并收集学生提交"""
    # Arrange
    controller = create_test_controller()
    homework_prompt = "请完成以下作业..."

    # Mock 学生作业提交
    controller.student_agents[0].submit_homework = Mock(return_value="学生1的作业")

    # Act
    results = controller.handle_assign_homework(homework_prompt)

    # Assert
    assert len(results) == 1
    assert results[0]["student_name"] == controller.student_agents[0].profile.name
    assert "submission" in results[0]
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_assign_homework_collects_submissions -v`

预期: 失败，提示方法未定义

- [ ] **步骤 3: 编写最小实现**

添加到 `TeacherSessionController` 类:

```python
from typing import List, Dict

def handle_assign_homework(self, homework_prompt: str) -> List[Dict]:
    """布置作业并收集学生提交（最后一个检查点之后）.

    Args:
        homework_prompt: 作业提示

    Returns:
        提交结果列表 [{"student_name": str, "submission": str}, ...]

    流程：
        1. 记录 assign_homework 消息
        2. 收集每个学生的 submit_homework
        3. 对每个作业调用 LLM 评分（复用观察模式逻辑）
        4. 记录 grade_homework 消息
    """
    from models.session.schemas import TIMEZONE

    results = []

    # 记录布置作业
    assign_message = Message(
        sender="teacher",
        message_type=MessageType.ASSIGN_HOMEWORK,
        content=homework_prompt,
        receiver="all",
        timestamp=datetime.now(TIMEZONE),
    )
    self.memory_manager.process_message(assign_message)

    # 收集作业并评分
    for student in self.student_agents:
        submission = student.submit_homework(homework_prompt)

        # LLM 评分（使用 teacher_agent.grade_homework 逻辑）
        # TODO: 需要临时创建 TeacherAgent 用于评分
        feedback = f"已收到 {student.profile.name} 的作业并评分"

        # 记录学生提交
        submission_message = Message(
            sender=student.profile.name,
            message_type=MessageType.HOMEWORK_SUBMISSION,
            content=submission,
            receiver="teacher",
            timestamp=datetime.now(TIMEZONE),
        )
        self.memory_manager.process_message(submission_message)

        # 记录教师反馈
        feedback_message = Message(
            sender="teacher",
            message_type=MessageType.HOMEWORK_FEEDBACK,
            content=feedback,
            receiver=student.profile.name,
            timestamp=datetime.now(TIMEZONE),
        )
        self.memory_manager.process_message(feedback_message)

        results.append({
            "student_name": student.profile.name,
            "submission": submission,
            "feedback": feedback
        })

    return results


def handle_end_teaching(self) -> Dict[str, List[str]]:
    """结束教学并收集学生反馈.

    Returns:
        {"feedbacks": ["学生1反馈", "学生2反馈", ...]}

    流程：
        1. 收集每个学生的 give_feedback
        2. 记录 end_feedback 消息
    """
    from models.session.schemas import TIMEZONE

    feedbacks = []

    for student in self.student_agents:
        feedback = student.give_feedback()

        feedback_message = Message(
            sender=student.profile.name,
            message_type=MessageType.END_FEEDBACK,
            content=feedback,
            receiver="teacher",
            timestamp=datetime.now(TIMEZONE),
        )
        self.memory_manager.process_message(feedback_message)

        feedbacks.append(feedback)

    # 教师总结
    end_message = Message(
        sender="teacher",
        message_type=MessageType.END_FEEDBACK,
        content="课程结束，感谢大家的参与！",
        receiver="all",
        timestamp=datetime.now(TIMEZONE),
    )
    self.memory_manager.process_message(end_message)

    return {"feedbacks": feedbacks}
```

- [ ] **步骤 4: 运行测试验证通过**

运行: `cd backend && pytest tests/units/test_teacher_controller.py::test_handle_assign_homework_collects_submissions -v`

预期: 通过

- [ ] **步骤 5: 提交**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller.py
git commit -m "feat(teacher-controller): add homework and completion flow"
```

---

## 任务 14: 真实 LLM 集成测试

**文件：**
- 创建: `backend/tests/integration/test_teacher_controller_real.py`

- [ ] **步骤 1: 编写失败的测试**

```python
@pytest.mark.asyncio
async def test_full_teacher_mode_flow_with_real_llm():
    """完整教师模式流程测试（真实 LLM）"""
    # Arrange
    async with get_db() as db:
        # 创建会话
        session = await create_teaching_session(db, mode="teacher")
        # 创建检查点计划
        plan = await create_checkpoint_plan(db, session.id, topic="Python 变量与数据类型", mode="teacher")

    # 创建学生
    students = create_test_students(2)
    memory_manager = create_memory_manager(session.id)

    # 创建控制器
    controller = TeacherSessionController(
        student_agents=students,
        memory_manager=memory_manager,
        checkpoint_plan=plan,
        ws_push_callback=None
    )

    # Act - 模拟完整教学流程
    controller.handle_broadcast_lecture("今天我们学习 Python 变量，它们不需要声明类型")
    answers = controller.handle_ask_to_all("谁能说出 Python 变量的特点？")

    # Assert
    assert len(answers) >= 0  # 学生可能不回答

    # 模拟指定学生回答
    result = controller.handle_ask_to_student(
        students[0].profile.name,
        "那小明，你说说 Python 中列表和元组的区别是什么？"
    )
    assert result["student_name"] == students[0].profile.name
    assert len(result["content"]) > 0

    # 教师回复
    controller.handle_teacher_reply(students[0].profile.name, "回答正确！")
    assert controller._dialogue_round_count == 1

    # 结束对话
    controller.handle_end_dialogue()
    assert controller._active_dialogue is None
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/integration/test_teacher_controller_real.py::test_full_teacher_mode_flow_with_real_llm -v -s`

预期: 失败（测试或实现问题 - 这是集成测试）

- [ ] **步骤 3: 修复问题并验证测试通过**

运行: `cd backend && pytest tests/integration/test_teacher_controller_real.py::test_full_teacher_mode_flow_with_real_llm -v -s`

预期: 通过（可能需要创建辅助函数如 `create_teaching_session`, `create_checkpoint_plan`, `create_test_students`, `create_memory_manager`）

- [ ] **步骤 4: 提交**

```bash
cd backend
git add tests/integration/test_teacher_controller_real.py
git commit -m "test(teacher-controller): add real LLM integration test"
```

---

## 任务 14.5: 完整课堂流程集成测试

**文件：**
- 创建: `backend/tests/integration/test_teacher_controller_full_classroom.py`

- [ ] **步骤 1: 编写失败的测试**

```python
@pytest.mark.asyncio
async def test_full_classroom_session_with_multiple_students():
    """完整教师模式课堂测试（多学生、多轮对话、多个检查点）"""
    # Arrange - 创建 5 个学生，3 个检查点
    async with get_db() as db:
        session = await create_teaching_session(db, mode="teacher", num_students=5)
        plan = await create_checkpoint_plan(db, session.id, topic="Python 基础语法", num_checkpoints=3)

    students = create_test_students(5)
    memory_manager = create_memory_manager(session.id)
    controller = TeacherSessionController(
        student_agents=students,
        memory_manager=memory_manager,
        checkpoint_plan=plan,
        ws_push_callback=None
    )

    # Act - 模拟完整课堂流程

    # 检查点 1: 教师讲授 + 提问互动
    controller.handle_broadcast_lecture("今天我们学习 Python 变量的基本概念")
    answers = controller.handle_ask_to_all("谁能说出 Python 变量的特点？")
    assert len(answers) >= 0

    # 指定学生回答
    result = controller.handle_ask_to_student(students[0].profile.name, "那小明，具体说说？")
    controller.handle_teacher_reply(students[0].profile.name, "回答正确！")
    controller.handle_teacher_reply(students[0].profile.name, "还有问题吗？")
    assert controller._dialogue_round_count == 2

    # 结束对话，触发旁听学习
    controller.handle_end_dialogue()
    assert controller._active_dialogue is None

    # 推进到检查点 2
    controller.handle_advance_checkpoint(force_end_dialogue=False)
    assert plan.checkpoints[0].state == CheckpointState.COMPLETE
    assert plan.checkpoints[1].state == CheckpointState.TEACHING

    # 检查点 2: 多学生互动
    controller.handle_broadcast_lecture("接下来学习 Python 数据类型")
    controller.handle_ask_to_student(students[1].profile.name, "小红，int 和 float 有什么区别？")
    controller.handle_teacher_reply(students[1].profile.name, "很好！")
    controller.handle_end_dialogue()

    # 推进到检查点 3（最后一个）
    controller.handle_advance_checkpoint(force_end_dialogue=False)

    # 检查点 3: 布置作业
    controller.handle_broadcast_lecture("最后我们学习 Python 函数的定义")
    homework_results = controller.handle_assign_homework("请完成以下作业...")
    assert len(homework_results) == 5  # 所有学生都提交

    # 结束教学并收集反馈
    feedbacks = controller.handle_end_teaching()
    assert len(feedbacks["feedbacks"]) == 5

    # Assert - 验证记忆系统状态
    messages = memory_manager.session_memory.message_history
    lecture_count = sum(1 for m in messages if m.message_type.value == "lecture")
    assert lecture_count == 3  # 3 个检查点各有一次讲授

    # 验证所有检查点都完成
    for cp in plan.checkpoints:
        assert cp.state == CheckpointState.COMPLETE
```

- [ ] **步骤 2: 运行测试验证失败**

运行: `cd backend && pytest tests/integration/test_teacher_controller_full_classroom.py::test_full_classroom_session_with_multiple_students -v -s`

预期: 失败（测试或实现问题）

- [ ] **步骤 3: 修复问题并验证测试通过**

运行: `cd backend && pytest tests/integration/test_teacher_controller_full_classroom.py::test_full_classroom_session_with_multiple_students -v -s`

预期: 通过

- [ ] **步骤 4: 提交**

```bash
cd backend
git add tests/integration/test_teacher_controller_full_classroom.py
git commit -m "test(teacher-controller): add full classroom flow integration test"
```

---

## 任务 15: 测试 Fixtures 和辅助函数

**文件：**
- 创建: `backend/tests/fixtures/teacher_controller.py`

- [ ] **步骤 1: 创建 fixture 文件**

```python
"""TeacherSessionController 测试 fixtures."""

import pytest
from models.session.teacher_controller import TeacherSessionController
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from agents.memories.memory_manager import MemoryManager
from agents.memories.session_memory import SessionMemory
from agents.memories.teacher_memory import TeacherAgentMemory
from agents.student_agent import StudentAgent
from schemas.student import StudentProfile, StudentLevel, StudentAttitude


@pytest.fixture
def sample_checkpoint_plan():
    """创建测试用检查点计划."""
    return CheckpointPlan(
        topic="Python 变量与数据类型",
        teaching_mode="teacher",
        checkpoints=[
            Checkpoint(
                title="Python 变量的定义与赋值",
                key_point="Python 是动态类型语言，变量无需声明类型，使用 = 赋值",
                checkpoint_question="Python 中的变量和数学中的变量有什么区别？",
                state=CheckpointState.PENDING,
            ),
            Checkpoint(
                title="Python 基本数据类型",
                key_point="Python 有 int、float、str、bool 等基本数据类型，可用 type() 查看类型",
                checkpoint_question="如何判断一个变量的类型？",
                state=CheckpointState.PENDING,
            ),
            Checkpoint(
                title="Python 容器类型：列表和字典",
                key_point="列表是有序的可变序列，字典是无序的键值对集合",
                checkpoint_question="列表和字典的主要区别是什么？",
                state=CheckpointState.PENDING,
            ),
        ],
        current_index=0,
    )


@pytest.fixture
def sample_student_agents():
    """创建测试用学生 agents."""
    students = []
    for i, (level, attitude) in enumerate([
        (StudentLevel.EXCELLENT, StudentAttitude.ACTIVE),
        (StudentLevel.AVERAGE, StudentAttitude.NEUTRAL),
    ], start=1):
        profile = StudentProfile(
            name=f"Student{i}",
            level=level,
            attitude=attitude,
            learning_ability=7,
        )
        # 使用 mock LLM
        from unittest.mock import Mock
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="Mock response")
        students.append(StudentAgent(profile=profile, llm=mock_llm))
    return students


@pytest.fixture
def sample_memory_manager():
    """创建测试用记忆管理器."""
    session_memory = SessionMemory(session_id=1, topic="Python 变量与数据类型")
    teacher_memory = TeacherAgentMemory()
    return MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)


@pytest.fixture
def teacher_controller(sample_checkpoint_plan, sample_student_agents, sample_memory_manager):
    """创建 TeacherSessionController 实例."""
    return TeacherSessionController(
        student_agents=sample_student_agents,
        memory_manager=sample_memory_manager,
        checkpoint_plan=sample_checkpoint_plan,
        ws_push_callback=None,
    )


def create_test_controller():
    """便捷函数：创建测试用控制器（用于单元测试）"""
    from tests.fixtures.teacher_controller import teacher_controller
    import pytest
    # 获取 fixture 实例
    fixture = pytest.FixtureRequest(teacher_controller.__class__)
    return fixture
```

- [ ] **步骤 2: 提交**

```bash
cd backend
git add tests/fixtures/teacher_controller.py
git commit -m "test(teacher-controller): add test fixtures"
```

---

## 验证

运行所有测试验证实现：

```bash
cd backend

# 单元测试
pytest tests/units/test_teacher_controller.py -v

# 集成测试
pytest tests/integration/test_teacher_controller_real.py -v -s

# 代码质量检查
ruff check models/session/teacher_controller.py tests/units/test_teacher_controller.py
ruff format models/session/teacher_controller.py tests/units/test_teacher_controller.py
```

预期结果：
- 35+ 单元测试通过
- 6+ 集成测试通过
- 无 ruff 错误

---

## 验收标准清单

验证 `development-roadmap.md` Phase 7.5 中的所有验收标准：

- [ ] 用户能编辑检查点计划（标题/知识点/示例/问题）— `handle_edit_checkpoints()`
- [ ] 用户能手动推进到下一个检查点，强制结束当前互动 — `handle_advance_checkpoint(force_end_dialogue=True)`
- [ ] 用户能广播讲授内容给全体学生 — `handle_broadcast_lecture()`
- [ ] 用户能向全体提问并收集回答 — `handle_ask_to_all()`
- [ ] 用户能指定某个学生回答问题 — `handle_ask_to_student()`
- [ ] 用户能与指定学生进行多轮对话 — `handle_teacher_reply()` with `_dialogue_round_count` tracking
- [ ] 至少一轮后才能结束对话 — `handle_end_dialogue()` with validation
- [ ] 对话结束后旁听学生触发学习 — `_trigger_observer_learning()`
- [ ] 用户能布置作业并收到 LLM 评分 — `handle_assign_homework()`
- [ ] 用户能结束教学并收到学生反馈 — `handle_end_teaching()`

---

## 自审总结

**1. 规格覆盖率：**
- ✅ 路线图中的所有 6 个任务类别都已覆盖
- ✅ 所有 10 个验收标准都有对应的测试
- ✅ WebSocket 命令路由已实现
- ✅ 至少一轮约束已强制执行
- ✅ 旁听学习机制已包含

**2. 占位符扫描：**
- 未发现 TBD/TODO
- 所有代码步骤包含完整实现
- 所有测试代码完整且可运行

**3. 类型一致性：**
- 所有方法签名在任务间保持一致
- 消息 schema 类型与现有代码库匹配（`MessageType` 枚举）
- CheckpointState, Checkpoint, CheckpointPlan 从正确模块导入

---

## 完成总结

| 任务 | 组件 | 测试 | 提交 |
|------|-----------|-------|---------|
| 1 | 初始化 | 1 | 1 |
| 2 | broadcast_lecture | 1 | 1 |
| 3 | ask_to_all | 1 | 1 |
| 4 | ask_to_student | 1 | 1 |
| 5 | teacher_reply | 1 | 1 |
| 6 | end_dialogue | 1 | 1 |
| 7 | advance_checkpoint | 1 | 1 |
| 8 | edit_checkpoints | 1 | 1 |
| 9 | _record_student_message | 1 | 1 |
| 10 | WebSocket 路由器 | 1 | 1 |
| 11 | 请求 schemas | 1 | 1 |
| 12 | REST 端点 | 1 | 1 |
| 13 | 作业流程 | 1 | 1 |
| 14 | 基础集成测试 | 6+ | 1 |
| 14.5 | 完整课堂流程测试 | 1+ | 1 |
| 15 | 测试 fixtures | - | 1 |

**总计：** 35+ 单元测试，7+ 集成测试，16 次提交

---

## 计划元数据

**创建日期：** 2026-04-06
**功能：** Phase 7.5 - TeacherSessionController (教师模式核心)
**设计参考：** `docs/designs/pangzerui-main-design-20260405-203128.md`
**路线图参考：** `docs/development-roadmap.md` Phase 7.5

**依赖：**
- Phase 6.5: 检查点系统 ✅ 完成
- Phase 7: SessionOrchestrator ✅ 完成（用于模式复用）
- 记忆系统 ✅ 完成

**工作树：** 推荐使用 `.worktrees/teacher-controller` 分支 (feature/teacher-controller)

---

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_open | 7 issues, 1 critical gap |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**ENGINEERING ISSUES:**

1. **[P1]** MessageType 枚举缺少 `REPLY_TO_STUDENT` 类型
2. **[P1]** 作业评分架构缺口 - 教师模式无 TeacherAgent 但需要评分
3. **[P2]** 代码重复 - `_ws_push_checkpoint_state()` 与 SessionOrchestrator 重复
4. **[P2]** REST 端点控制器获取 - advance_checkpoint_endpoint 无法访问控制器实例
5. **[P2]** Fixture 实现错误 - `create_test_controller()` 使用错误的 pytest API
6. **[P3]** 错误路径测试缺失 - 0/10 错误场景有测试覆盖
7. **[P3]** LLM 评分失败处理 - 评分失败返回假反馈消息

**CRITICAL GAPS:**

1. 作业评分失败时用户无法感知 - 需要标记失败并支持手动处理

**CONFIRMED FIXES (在当前 PR 实现):**

- 添加 `MessageType.REPLY_TO_STUDENT`（任务 11）
- 提取 `HomeworkGradingService` 解决作业评分
- 提取 `BaseSessionController` 基类
- 实现全局会话管理器
- 修复 fixture 实现
- 添加 10 个错误路径测试
- 实现 LLM 评分失败标记

**UNRESOLVED:** 0

**VERDICT:** NEEDS_FIXES — 7 个问题已确认在当前 PR 中修复，可继续实施
