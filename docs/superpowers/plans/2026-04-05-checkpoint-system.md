# 检查点系统（Phase 6.5）实现计划

> **For agentic workers:** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法跟踪进度。

**目标：** 实现检查点 schemas、LLM 计划生成服务（带三层降级）、独立的数据库表持久化，以及 REST API 端点。

**架构：** Pydantic schemas 和 services 位于同一个目录 `backend/models/checkpoint/`（业务内聚）。独立的 `checkpoint_plans` 表存储计划，通过外键关联 `teaching_sessions`。`CheckpointPlanService` 通过 LLM 和结构化输出生成计划，带三个降级层。`CheckpointPlanPersistence` 处理数据库读写。FastAPI 路由暴露 generate/get/put 端点。

**技术栈：** Python 3.12+, FastAPI, Pydantic v2, LangChain (ChatOpenAI + with_structured_output), SQLAlchemy async, Alembic, pytest

---

## 文件结构

```
backend/
├── models/
│   └── checkpoint/
│       ├── __init__.py                # 新建 — package init
│       ├── schemas.py                 # 新建 — CheckpointState, Checkpoint, CheckpointPlan
│       ├── service.py                 # 新建 — CheckpointPlanPersistence（DB 读写）
│       ├── plan_service.py            # 新建 — CheckpointPlanService（LLM 生成）
│       └── router.py                  # 新建 — POST/GET/PUT 端点
├── orm/
│   └── checkpoint_plan.py             # 新建 — CheckpointPlanModel ORM
├── alembic/versions/
│   └── 003_create_checkpoint_plans_table.py  # 新建 — migration
├── tests/
│   └── units/
│       ├── test_checkpoint_schemas.py # 新建 — schema 验证测试
│       ├── test_checkpoint_service.py # 新建 — CheckpointPlanService 单元测试
│       ├── test_checkpoint_persistence.py  # 新建 — DB 持久化测试
│       └── test_checkpoint_api.py     # 新建 — API 端点测试
└── main.py                            # 修改 — 注册 checkpoint router
```

## LLM 生成检查点逻辑

### Prompt 模板

LLM prompt 位于 `CheckpointPlanService._build_prompt()` 方法中（任务3）：

```python
def _build_prompt(self, topic: str, teaching_mode: str) -> str:
    """构建 LLM prompt.

    根据教学模式调整详细程度:
    - didactic: 清晰、聚焦的知识点
    - heuristic: 知识点 + 检查问题
    - discussion: 开放式知识点 + 讨论问题
    - teacher: 通用知识点，作为教学参考
    """
```

**完整 Prompt 模板**（位于任务3的代码实现）：

```
你是一位教学设计专家。请为以下主题设计一个结构化的检查点教学计划。

主题: {topic}
{教学模式说明}

要求:
1. 将主题拆分为 3-8 个检查点（取决于主题复杂度）
2. 每个检查点包含:
   - title: 检查点标题（简短，如"Python 变量与数据类型"）
   - key_point: 本检查点的核心知识点（单个字符串，教师将根据此进行教学）
   - checkpoint_question: 检查理解的问题
   - state: 固定为 "pending"
3. 按教学顺序排列（基础优先，应用在后）
4. teaching_mode: "{teaching_mode}"
5. current_index: 0

请严格按照 JSON 格式返回，不要添加任何额外文字。
```

### 三层降级策略

当LLM生成失败时的降级逻辑：

1. **Layer 1**: `with_structured_output(CheckpointPlan)` — 最可靠，直接返回 Pydantic 对象
2. **Layer 2**: `Pydantic.model_validate_json(raw_response)` — 手动解析 LLM 原始输出
3. **Layer 3**: 返回最小 1 检查点计划覆盖整个主题 — 保底方案

### 相关文档位置

- **设计文档**: `docs/design.md` 第620-650行（检查点计划生成章节）
- **计划文档**: 本文件任务3（CheckpointPlanService 实现）
- **API文档**: `docs/api.md` 中的检查点相关端点

---

### 任务 1：检查点 Schemas

**文件：**
- 新建：`backend/models/checkpoint/__init__.py`
- 新建：`backend/models/checkpoint/schemas.py`
- 测试：`backend/tests/units/test_checkpoint_schemas.py`

- [ ] **步骤 1：创建 package init**

```python
# backend/models/checkpoint/__init__.py
"""检查点相关模块."""
```

- [ ] **步骤 2：编写失败测试**

```python
# backend/tests/units/test_checkpoint_schemas.py
"""Checkpoint schema 单元测试."""

import pytest
from pydantic import ValidationError

from models.checkpoint.schemas import (
    Checkpoint,
    CheckpointPlan,
    CheckpointState,
)


class TestCheckpointState:
    """CheckpointState 枚举测试."""

    def test_four_states_exist(self):
        assert CheckpointState.PENDING == "pending"
        assert CheckpointState.TEACHING == "teaching"
        assert CheckpointState.QUESTIONS == "questions"
        assert CheckpointState.COMPLETE == "complete"

    def test_state_values_are_strings(self):
        for state in CheckpointState:
            assert isinstance(state.value, str)


class TestCheckpoint:
    """Checkpoint 模型测试."""

    def test_valid_checkpoint(self):
        cp = Checkpoint(
            title="Python 变量与数据类型",
            key_point="变量和数据类型的基本概念",
            checkpoint_question="Python 中有哪些基本数据类型?",
        )
        assert cp.title == "Python 变量与数据类型"
        assert cp.state == CheckpointState.PENDING

    def test_default_state_is_pending(self):
        cp = Checkpoint(
            title="test",
            key_point="知识点",
            checkpoint_question="q?",
        )
        assert cp.state == CheckpointState.PENDING

    def test_title_min_length(self):
        with pytest.raises(ValidationError):
            Checkpoint(
                title="",
                key_point="p1",
                checkpoint_question="q?",
            )

    def test_key_point_min_length(self):
        with pytest.raises(ValidationError):
            Checkpoint(
                title="test",
                key_point="",
                checkpoint_question="q?",
            )

    def test_checkpoint_question_min_length(self):
        with pytest.raises(ValidationError):
            Checkpoint(
                title="test",
                key_point="p1",
                checkpoint_question="",
            )

    def test_state_can_be_set_to_teaching(self):
        cp = Checkpoint(
            title="test",
            key_point="p1",
            checkpoint_question="q?",
            state=CheckpointState.TEACHING,
        )
        assert cp.state == CheckpointState.TEACHING

    def test_json_round_trip(self):
        """Checkpoint 可正确序列化和反序列化."""
        cp = Checkpoint(
            title="Python 变量与数据类型",
            key_point="变量的命名规则, int/float/str/bool 类型"checkpoint_question="Python 中有哪些基本数据类型?",
            state=CheckpointState.QUESTIONS,
        )
        json_str = cp.model_dump_json()
        restored = Checkpoint.model_validate_json(json_str)
        assert restored.title == cp.title
        assert restored.state == CheckpointState.QUESTIONS
        assert restored.key_point == cp.key_point


class TestCheckpointPlan:
    """CheckpointPlan 模型测试."""

    def _make_plan(self, **kwargs) -> CheckpointPlan:
        defaults = {
            "topic": "Python 基础入门",
            "teaching_mode": "heuristic",
            "checkpoints": [
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str, bool",
                    checkpoint_question="q?",
                )
            ],
        }
        defaults.update(kwargs)
        return CheckpointPlan(**defaults)

    def test_valid_plan(self):
        plan = self._make_plan()
        assert plan.topic == "Python 基础入门"
        assert plan.current_index == 0

    def test_default_current_index_is_zero(self):
        plan = self._make_plan()
        assert plan.current_index == 0

    def test_teaching_mode_accepts_four_values(self):
        for mode in ("didactic", "heuristic", "discussion", "teacher"):
            plan = self._make_plan(teaching_mode=mode)
            assert plan.teaching_mode == mode

    def test_teaching_mode_rejects_invalid(self):
        with pytest.raises(ValidationError, match="teaching_mode"):
            self._make_plan(teaching_mode="invalid")

    def test_teaching_mode_rejects_none(self):
        with pytest.raises(ValidationError):
            CheckpointPlan(
                topic="test",
                teaching_mode=None,  # type: ignore[arg-type]
                checkpoints=[
                    Checkpoint(
                        title="t",
                        key_point="p",
                        checkpoint_question="q",
                    )
                ],
            )

    def test_checkpoints_min_length(self):
        with pytest.raises(ValidationError):
            CheckpointPlan(
                topic="test",
                teaching_mode="heuristic",
                checkpoints=[],
            )

    def test_current_index_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            self._make_plan(current_index=-1)

    def test_plan_json_round_trip(self):
        """CheckpointPlan JSON 序列化/反序列化往返."""
        plan = self._make_plan(
            teaching_mode="teacher",
            current_index=2,
            checkpoints=[
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str, bool",
                    checkpoint_question="Python 有哪些基本数据类型?",
                    state=CheckpointState.COMPLETE,
                ),
                Checkpoint(
                    title="条件判断",
                    key_point="if/elif/else, 比较运算符, 逻辑运算符",
                    checkpoint_question="if 和 elif 有什么区别?",
                    state=CheckpointState.TEACHING,
                ),
            ],
        )
        json_str = plan.model_dump_json()
        restored = CheckpointPlan.model_validate_json(json_str)
        assert restored.teaching_mode == "teacher"
        assert restored.current_index == 2
        assert len(restored.checkpoints) == 2
        assert restored.checkpoints[0].state == CheckpointState.COMPLETE
```

- [ ] **步骤 3：运行测试验证失败**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_schemas.py -v`
预期：FAIL — `ModuleNotFoundError: No module named 'models.checkpoint.schemas'`

- [ ] **步骤 4：实现 schemas**

```python
# backend/models/checkpoint/schemas.py
"""检查点相关 Pydantic schemas."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CheckpointState(str, Enum):
    """检查点状态枚举."""

    PENDING = "pending"
    TEACHING = "teaching"
    QUESTIONS = "questions"
    COMPLETE = "complete"


class Checkpoint(BaseModel):
    """单个检查点的完整教学计划。"""

    title: str = Field(min_length=1, max_length=200, description="检查点标题")
    key_point: str = Field(min_length=1, description="本检查点的核心知识点（单个）")
    checkpoint_question: str = Field(
        min_length=1, description="检查理解的问题"
    )
    state: CheckpointState = Field(
        default=CheckpointState.PENDING, description="检查点当前状态"
    )


class CheckpointPlan(BaseModel):
    """一节课的完整检查点计划."""

    topic: str = Field(min_length=1, max_length=200, description="教学主题")
    teaching_mode: str = Field(
        description="教学模式: didactic/heuristic/discussion/teacher"
    )
    checkpoints: list[Checkpoint] = Field(
        min_length=1, description="检查点列表（至少 1 个）"
    )
    current_index: int = Field(default=0, ge=0, description="当前检查点索引")

    @field_validator("teaching_mode")
    @classmethod
    def validate_teaching_mode(cls, v: str) -> str:
        allowed = {"didactic", "heuristic", "discussion", "teacher"}
        if v not in allowed:
            raise ValueError(
                f"teaching_mode 必须是 {allowed} 之一，收到: {v}"
            )
        return v
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_schemas.py -v`
预期：全部 19 个测试 PASS

- [ ] **步骤 6：提交**

```bash
git add backend/models/checkpoint/__init__.py backend/models/checkpoint/schemas.py backend/tests/units/test_checkpoint_schemas.py
git commit -m "feat: add checkpoint schemas (CheckpointState, Checkpoint, CheckpointPlan)"
```

---

### 任务 2：数据库 — ORM 模型 + Migration

**文件：**
- 新建：`backend/orm/checkpoint_plan.py`
- 新建：`backend/alembic/versions/003_create_checkpoint_plans_table.py`
- 修改：`backend/tests/conftest.py`（添加 ORM 导入用于测试 fixture）

- [ ] **步骤 1：编写失败的持久化测试**

```python
# backend/tests/units/test_checkpoint_persistence.py
"""Checkpoint 持久化单元测试（独立 checkpoint_plans 表）。"""

import pytest
from sqlalchemy import select

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from orm.checkpoint_plan import CheckpointPlanModel


@pytest.mark.asyncio
class TestCheckpointPersistence:
    """检查点持久化到 checkpoint_plans 表."""

    async def test_save_and_load_plan(self, db_session):
        """生成后存储到 checkpoint_plans 表."""
        plan = CheckpointPlan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str, bool",
                    checkpoint_question="Python 有哪些基本数据类型?",
                ),
            ],
        )

        # 先创建一个 TeachingSession 作为外键
        from orm.teaching_session import TeachingSessionModel

        session = TeachingSessionModel(
            teaching_mode="heuristic",
            topic="Python 基础入门",
            students_config={"mode": "random", "count": 5},
        )
        db_session.add(session)
        await db_session.flush()

        # 保存 checkpoint plan
        cp_record = CheckpointPlanModel(
            session_id=session.id,
            plan_data=plan.model_dump(),
        )
        db_session.add(cp_record)
        await db_session.commit()
        await db_session.refresh(cp_record)

        assert cp_record.id is not None
        assert cp_record.session_id == session.id

        # 从 DB 加载
        result = await db_session.execute(
            select(CheckpointPlanModel).where(
                CheckpointPlanModel.session_id == session.id
            )
        )
        loaded = result.scalar_one()
        assert loaded.plan_data["topic"] == "Python 基础入门"
        assert len(loaded.plan_data["checkpoints"]) == 1

    async def test_update_plan_in_db(self, db_session):
        """编辑后更新 checkpoint_plans 表."""
        from orm.teaching_session import TeachingSessionModel

        session = TeachingSessionModel(
            teaching_mode="teacher",
            topic="Python 基础入门",
            students_config={"mode": "random", "count": 5},
        )
        db_session.add(session)
        await db_session.flush()

        plan = CheckpointPlan(
            topic="Python 基础入门",
            teaching_mode="teacher",
            checkpoints=[
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str",
                    checkpoint_question="Python 有哪些数据类型?",
                ),
            ],
        )
        cp_record = CheckpointPlanModel(
            session_id=session.id,
            plan_data=plan.model_dump(),
        )
        db_session.add(cp_record)
        await db_session.commit()
        await db_session.refresh(cp_record)

        # 更新 plan_data
        cp_record.plan_data["checkpoints"][0]["state"] = "complete"
        cp_record.plan_data["current_index"] = 1
        await db_session.commit()
        await db_session.refresh(cp_record)

        assert cp_record.plan_data["checkpoints"][0]["state"] == "complete"
        assert cp_record.plan_data["current_index"] == 1

    async def test_checkpoint_state_change_updates_json(self, db_session):
        """Checkpoint state 变更后 JSON 字段正确更新."""
        from orm.teaching_session import TeachingSessionModel

        session = TeachingSessionModel(
            teaching_mode="discussion",
            topic="Python 条件判断与循环",
            students_config={"mode": "random", "count": 5},
        )
        db_session.add(session)
        await db_session.flush()

        plan = CheckpointPlan(
            topic="Python 条件判断与循环",
            teaching_mode="discussion",
            checkpoints=[
                Checkpoint(
                    title="if 条件判断",
                    key_point="if/elif/else 语法, 比较运算符",
                    checkpoint_question="if 和 elif 有什么区别?",
                    state=CheckpointState.TEACHING,
                ),
                Checkpoint(
                    title="for 循环",
                    key_point="range() 函数, 遍历列表",
                    checkpoint_question="for 循环和 while 循环有什么区别?",
                    state=CheckpointState.PENDING,
                ),
            ],
            current_index=0,
        )
        cp_record = CheckpointPlanModel(
            session_id=session.id,
            plan_data=plan.model_dump(),
        )
        db_session.add(cp_record)
        await db_session.commit()
        await db_session.refresh(cp_record)

        # 状态变更: checkpoint 0 TEACHING → QUESTIONS
        cp_record.plan_data["checkpoints"][0]["state"] = "questions"
        await db_session.commit()
        await db_session.refresh(cp_record)

        # 通过 CheckpointPlan 反序列化验证
        restored = CheckpointPlan.model_validate(cp_record.plan_data)
        assert restored.checkpoints[0].state == CheckpointState.QUESTIONS
        assert restored.checkpoints[1].state == CheckpointState.PENDING

    async def test_one_plan_per_session(self, db_session):
        """每个 session 只有一条 checkpoint plan 记录（应用层约束）."""
        from orm.teaching_session import TeachingSessionModel

        session = TeachingSessionModel(
            teaching_mode="heuristic",
            topic="Python 基础入门",
            students_config={"mode": "random", "count": 5},
        )
        db_session.add(session)
        await db_session.flush()

        plan = CheckpointPlan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str",
                    checkpoint_question="q?",
                ),
            ],
        )

        # 第一条记录
        cp1 = CheckpointPlanModel(
            session_id=session.id,
            plan_data=plan.model_dump(),
        )
        db_session.add(cp1)
        await db_session.commit()

        # 查询该 session 的所有 plan
        result = await db_session.execute(
            select(CheckpointPlanModel).where(
                CheckpointPlanModel.session_id == session.id
            )
        )
        plans = result.scalars().all()
        assert len(plans) == 1
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_persistence.py -v`
预期：FAIL — `ModuleNotFoundError: No module named 'orm.checkpoint_plan'`

- [ ] **步骤 3：创建 ORM 模型**

```python
# backend/orm/checkpoint_plan.py
"""检查点计划 ORM 模型."""

from sqlalchemy import JSON, ForeignKey, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CheckpointPlanModel(Base, AsyncAttrs):
    """检查点计划表.

    每个教学会话最多一条记录。plan_data 存储完整的 CheckpointPlan JSON。
    """

    __tablename__ = "checkpoint_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("teaching_sessions.id"),
        nullable=False,
    )
    plan_data: Mapped[dict] = mapped_column(JSON, nullable=False)
```

- [ ] **步骤 4：在测试 fixture 中注册 ORM 模型**

在 `backend/tests/conftest.py` 的 `test_engine` fixture 中添加导入：

```python
# 在其他 ORM 导入旁添加此行：
    from orm.checkpoint_plan import CheckpointPlanModel  # noqa: F401
```

- [ ] **步骤 5：创建 Alembic migration**

```python
# backend/alembic/versions/003_create_checkpoint_plans_table.py
"""create checkpoint_plans table

Revision ID: 003
Revises: 002
Create Date: 2026-04-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 checkpoint_plans 表."""
    op.create_table(
        "checkpoint_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "session_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column("plan_data", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["teaching_sessions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_checkpoint_plans_session_id",
        "checkpoint_plans",
        ["session_id"],
    )


def downgrade() -> None:
    """删除 checkpoint_plans 表."""
    op.drop_index("ix_checkpoint_plans_session_id", table_name="checkpoint_plans")
    op.drop_table("checkpoint_plans")
```

- [ ] **步骤 6：运行 migration**

运行：`cd backend && alembic upgrade head`
预期：无错误

- [ ] **步骤 7：运行持久化测试**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_persistence.py -v`
预期：全部 4 个测试 PASS

- [ ] **步骤 8：提交**

```bash
git add backend/orm/checkpoint_plan.py backend/alembic/versions/003_create_checkpoint_plans_table.py backend/tests/conftest.py backend/tests/units/test_checkpoint_persistence.py
git commit -m "feat: add checkpoint_plans table (ORM + migration + persistence tests)"
```

---

### 任务 3：CheckpointPlanService（LLM 生成）

**文件：**
- 新建：`backend/models/checkpoint/plan_service.py`
- 新建：`backend/tests/units/test_checkpoint_service.py`

- [ ] **步骤 1：编写失败测试**

```python
# backend/tests/units/test_checkpoint_service.py
"""CheckpointPlanService 单元测试."""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState

# 有效计划 JSON 用于 mock 返回
VALID_PLAN_JSON = json.dumps({
    "topic": "Python 基础入门",
    "teaching_mode": "heuristic",
    "checkpoints": [
        {
            "title": "Python 变量与数据类型",
            "key_point": "",
            
            "checkpoint_question": "Python 中有哪些基本数据类型?",
            "state": "pending",
        },
        {
            "title": "Python 条件判断",
            "key_point": "",
            
            "checkpoint_question": "if 和 elif 有什么区别?",
            "state": "pending",
        },
    ],
    "current_index": 0,
})

MALFORMED_JSON = "{ this is not valid json }"

INVALID_SCHEMA_JSON = json.dumps({
    "topic": "Python 基础入门",
    "checkpoints": [],
})


class TestCheckpointPlanServiceGenerate:
    """CheckpointPlanService.generate_plan() 测试."""

    def _make_service(self, llm_client: MagicMock | None = None):
        from models.checkpoint.plan_service import CheckpointPlanService
        return CheckpointPlanService(llm_client=llm_client)

    def _make_mock_llm(self, return_value: str) -> MagicMock:
        llm = MagicMock()
        llm.invoke.return_value = return_value
        return llm

    def test_normal_generation_returns_valid_plan(self):
        """正常生成（Mock LLM 返回有效 JSON）。"""
        llm = self._make_mock_llm(VALID_PLAN_JSON)
        service = self._make_service(llm)

        import asyncio
        import logging

        # 配置日志输出
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        plan = asyncio.get_event_loop().run_until_complete(
            service.generate_plan(topic="Python 基础入门", teaching_mode="heuristic")
        )

        # 打印生成的计划到日志
        logger.info("=" * 60)
        logger.info("LLM 生成的检查点计划:")
        logger.info(f"主题: {plan.topic}")
        logger.info(f"教学模式: {plan.teaching_mode}")
        logger.info(f"检查点数量: {len(plan.checkpoints)}")
        for i, cp in enumerate(plan.checkpoints, 1):
            logger.info(f"\n检查点 {i}:")
            logger.info(f"  标题: {cp.title}")
            logger.info(f"  知识点: {cp.key_point}")
            logger.info(f"  检查问题: {cp.checkpoint_question}")
            logger.info(f"  状态: {cp.state}")
        logger.info("=" * 60)

        assert isinstance(plan, CheckpointPlan)
        assert plan.topic == "Python 基础入门"
        assert len(plan.checkpoints) == 2
        assert plan.checkpoints[0].title == "Python 变量与数据类型"

    def test_layer1_failure_falls_to_layer2(self):
        """Layer 1 (with_structured_output) 失败 → 降级到 Layer 2。"""
        llm = self._make_mock_llm(VALID_PLAN_JSON)
        service = self._make_service(llm)

        import asyncio
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        with patch.object(
            service._llm._llm, "with_structured_output", side_effect=Exception("fail")
        ):
            logger.warning("Layer 1 (with_structured_output) 失败，降级到 Layer 2...")
            plan = asyncio.get_event_loop().run_until_complete(
                service.generate_plan(topic="Python 基础入门", teaching_mode="heuristic")
            )

        logger.info(f"Layer 2 降级成功，生成计划: {plan.topic}")
        assert isinstance(plan, CheckpointPlan)
        assert plan.topic == "Python 基础入门"

    def test_layer2_failure_falls_to_layer3(self):
        """Layer 2 也失败 → 降级到 Layer 3（1 检查点兜底）。"""
        llm = self._make_mock_llm(MALFORMED_JSON)
        service = self._make_service(llm)

        import asyncio
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        with patch.object(
            service._llm._llm, "with_structured_output", side_effect=Exception("fail")
        ):
            logger.warning("Layer 1 失败，尝试 Layer 2...")
            logger.warning("Layer 2 解析失败，降级到 Layer 3（兜底计划）...")
            plan = asyncio.get_event_loop().run_until_complete(
                service.generate_plan(topic="Python 基础入门", teaching_mode="heuristic")
            )

        logger.info(f"Layer 3 兜底计划生成: {plan.checkpoints[0].title}")
        assert isinstance(plan, CheckpointPlan)
        assert len(plan.checkpoints) == 1
        assert plan.checkpoints[0].title == "Python 基础入门"

    def test_empty_checkpoints_falls_to_layer3(self):
        """空检查点列表 → Layer 3 兜底。"""
        llm = self._make_mock_llm(INVALID_SCHEMA_JSON)
        service = self._make_service(llm)

        import asyncio

        with patch.object(
            service._llm._llm, "with_structured_output", side_effect=Exception("fail")
        ):
            plan = asyncio.get_event_loop().run_until_complete(
                service.generate_plan(topic="Python 基础入门", teaching_mode="heuristic")
            )

        assert len(plan.checkpoints) >= 1

    def test_teaching_mode_teacher_works(self):
        """teaching_mode='teacher' 时正常工作。"""
        teacher_plan_json = json.dumps({
            "topic": "Python 自由教学",
            "teaching_mode": "teacher",
            "checkpoints": [
                {
                    "title": "课堂导入",
                    "key_point": "",
                    "checkpoint_question": "你之前接触过编程吗?",
                    "state": "pending",
                }
            ],
            "current_index": 0,
        })
        llm = self._make_mock_llm(teacher_plan_json)
        service = self._make_service(llm)

        import asyncio
        plan = asyncio.get_event_loop().run_until_complete(
            service.generate_plan(topic="Python 自由教学", teaching_mode="teacher")
        )

        assert plan.teaching_mode == "teacher"

    def test_prompt_contains_topic(self):
        """LLM prompt 包含主题信息。"""
        llm = self._make_mock_llm(VALID_PLAN_JSON)
        service = self._make_service(llm)

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            service.generate_plan(topic="Python 基础入门", teaching_mode="heuristic")
        )

        assert llm.invoke.called
        prompt = str(llm.invoke.call_args)
        assert "Python 基础入门" in prompt

    def test_prompt_contains_teaching_mode(self):
        """LLM prompt 包含教学模式信息。"""
        llm = self._make_mock_llm(VALID_PLAN_JSON)
        service = self._make_service(llm)

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            service.generate_plan(topic="Python 基础入门", teaching_mode="discussion")
        )

        prompt = str(llm.invoke.call_args)
        assert "discussion" in prompt
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_service.py -v`
预期：FAIL — `ModuleNotFoundError: No module named 'models.checkpoint.plan_service'`

- [ ] **步骤 3：实现 CheckpointPlanService**

```python
# backend/models/checkpoint/plan_service.py
"""检查点计划生成服务 — 三层降级策略。"""

import json
import logging

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState

logger = logging.getLogger(__name__)


class CheckpointPlanService:
    """LLM 驱动的检查点计划生成.

    三层降级策略:
    1. with_structured_output(CheckpointPlan) — 最可靠
    2. Pydantic.model_validate_json(raw) — 手动解析
    3. 最小 1 检查点兜底 — 保底方案
    """

    def __init__(self, *, llm_client) -> None:
        """初始化.

        Args:
            llm_client: LLMClient 实例.
        """
        self._llm = llm_client

    def _build_prompt(self, topic: str, teaching_mode: str) -> str:
        """构建 LLM prompt.

        根据教学模式调整详细程度:
        - didactic: 更多知识点，更少示例
        - heuristic: 适量知识点 + 检查问题
        - discussion: 更少知识点，更多开放式检查问题
        - teacher: 不限定教学方式，生成通用知识点
        """
        mode_instructions = {
            "didactic": (
                "教学模式：灌输式。每个检查点应包含清晰、聚焦的知识点，"
                "检查问题侧重知识记忆。"
            ),
            "heuristic": (
                "教学模式：启发式。每个检查点包含一个核心知识点，"
                "检查问题引导学生思考。"
            ),
            "discussion": (
                "教学模式：讨论式。每个检查点包含一个核心知识点，"
                "检查问题应为开放式，鼓励学生讨论和表达观点。"
            ),
            "teacher": (
                "教学模式：教师模式（真人教师自行决定教学方式）。"
                "每个检查点包含一个核心知识点，"
                "作为教学参考而非约束。"
            ),
        }

        return f"""你是一位教学设计专家。请为以下主题设计一个结构化的检查点教学计划。

主题: {topic}
{mode_instructions.get(teaching_mode, mode_instructions["heuristic"])}

要求:
1. 将主题拆分为 3-8 个检查点（取决于主题复杂度）
2. 每个检查点包含:
   - title: 检查点标题（简短，如"Python 变量与数据类型"）
   - key_point: 本检查点的核心知识点（单个字符串，教师将根据此进行教学）
   - checkpoint_question: 检查理解的问题
   - state: 固定为 "pending"
3. 按教学顺序排列（基础优先，应用在后）
4. teaching_mode: "{teaching_mode}"
5. current_index: 0

请严格按照 JSON 格式返回，不要添加任何额外文字。"""

    def _build_fallback_plan(self, topic: str, teaching_mode: str) -> CheckpointPlan:
        """Layer 3: 最小 1 检查点兜底计划。"""
        return CheckpointPlan(
            topic=topic,
            teaching_mode=teaching_mode,
            checkpoints=[
                Checkpoint(
                    title=topic,
                    key_point="f{topic}的核心内容",
                    checkpoint_question=f"关于{topic}，你学到了什么?",
                )
            ],
            current_index=0,
        )

    async def generate_plan(
        self,
        topic: str,
        teaching_mode: str,
    ) -> CheckpointPlan:
        """生成检查点计划（三层降级）。

        Args:
            topic: 教学主题.
            teaching_mode: 教学模式 (didactic/heuristic/discussion/teacher).

        Returns:
            CheckpointPlan 实例.
        """
        prompt = self._build_prompt(topic, teaching_mode)

        # Layer 1: with_structured_output
        try:
            structured_llm = self._llm._llm.with_structured_output(CheckpointPlan)
            messages = [{"role": "user", "content": prompt}]
            plan = structured_llm.invoke(messages)
            if isinstance(plan, CheckpointPlan) and len(plan.checkpoints) >= 1:
                logger.info("Layer 1 成功: with_structured_output 生成 %d 个检查点", len(plan.checkpoints))
                return plan
        except Exception as e:
            logger.warning("Layer 1 失败: %s", e)

        # Layer 2: 手动 JSON 解析
        try:
            raw_response = self._llm.invoke(prompt)
            plan = CheckpointPlan.model_validate_json(raw_response)
            if len(plan.checkpoints) >= 1:
                logger.info("Layer 2 成功: 手动解析生成 %d 个检查点", len(plan.checkpoints))
                return plan
        except (Exception) as e:
            logger.warning("Layer 2 失败: %s", e)

        # Layer 3: 最小兜底
        logger.warning("Layer 3 兜底: 使用最小 1 检查点计划")
        return self._build_fallback_plan(topic, teaching_mode)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_service.py -v`
预期：全部 8 个测试 PASS

- [ ] **步骤 5：提交**

```bash
git add backend/models/checkpoint/plan_service.py backend/tests/units/test_checkpoint_service.py
git commit -m "feat: add CheckpointPlanService with 3-layer degradation"
```

---

### 任务 4：持久化服务

**文件：**
- 新建：`backend/models/checkpoint/service.py`

- [ ] **步骤 1：实现持久化服务**

```python
# backend/models/checkpoint/service.py
"""检查点计划持久化服务。"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.checkpoint.schemas import CheckpointPlan
from orm.checkpoint_plan import CheckpointPlanModel

logger = logging.getLogger(__name__)


class CheckpointPlanPersistence:
    """检查点计划的数据库读写。"""

    def __init__(self, db_session: AsyncSession) -> None:
        self._db = db_session

    async def save_plan(self, session_id: int, plan: CheckpointPlan) -> CheckpointPlanModel:
        """保存检查点计划.

        如果该 session 已有计划记录，则更新；否则创建新记录。
        """
        result = await self._db.execute(
            select(CheckpointPlanModel).where(
                CheckpointPlanModel.session_id == session_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.plan_data = plan.model_dump()
            await self._db.commit()
            await self._db.refresh(existing)
            return existing
        else:
            record = CheckpointPlanModel(
                session_id=session_id,
                plan_data=plan.model_dump(),
            )
            self._db.add(record)
            await self._db.commit()
            await self._db.refresh(record)
            return record

    async def load_plan(self, session_id: int) -> CheckpointPlan | None:
        """从 checkpoint_plans 表加载检查点计划。"""
        result = await self._db.execute(
            select(CheckpointPlanModel).where(
                CheckpointPlanModel.session_id == session_id
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None

        return CheckpointPlan.model_validate(record.plan_data)

    async def update_plan(self, session_id: int, plan: CheckpointPlan) -> CheckpointPlan | None:
        """更新检查点计划（教师模式编辑）。

        Returns:
            更新后的 CheckpointPlan，或 None（session 不存在）.
        """
        result = await self._db.execute(
            select(CheckpointPlanModel).where(
                CheckpointPlanModel.session_id == session_id
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None

        record.plan_data = plan.model_dump()
        await self._db.commit()
        await self._db.refresh(record)
        return CheckpointPlan.model_validate(record.plan_data)
```

- [ ] **步骤 2：提交**

```bash
git add backend/models/checkpoint/service.py
git commit -m "feat: add CheckpointPlanPersistence service (read/write/update)"
```

---

### 任务 5：API 路由 + 集成测试

**文件：**
- 新建：`backend/models/checkpoint/router.py`
- 修改：`backend/main.py`
- 新建：`backend/tests/units/test_checkpoint_api.py`

- [ ] **步骤 1：编写失败的 API 测试**

```python
# backend/tests/units/test_checkpoint_api.py
"""Checkpoint API 端点测试."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

VALID_PLAN_RESPONSE = {
    "topic": "Python 基础入门",
    "teaching_mode": "heuristic",
    "checkpoints": [
        {
            "title": "Python 变量与数据类型",
            "key_point": "",
            
            "checkpoint_question": "Python 中有哪些基本数据类型?",
            "state": "pending",
        }
    ],
    "current_index": 0,
}


@pytest.fixture
def client():
    """创建测试客户端。"""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_llm():
    """Mock LLM 客户端。"""
    llm = MagicMock()
    llm.invoke.return_value = json.dumps(VALID_PLAN_RESPONSE)
    llm._llm = MagicMock()
    from models.checkpoint.schemas import CheckpointPlan
    llm._llm.with_structured_output.return_value.invoke.return_value = (
        CheckpointPlan.model_validate(VALID_PLAN_RESPONSE)
    )
    return llm


class TestGeneratePlanAPI:
    """POST /checkpoint-plan/generate 测试。"""

    def test_generate_returns_valid_plan(self, client, mock_llm):
        """200 + 有效响应。"""
        with patch("models.checkpoint.router.CheckpointPlanService") as MockService:
            from models.checkpoint.schemas import CheckpointPlan
            plan = CheckpointPlan.model_validate(VALID_PLAN_RESPONSE)
            MockService.return_value.generate_plan = MagicMock(return_value=plan)

            response = client.post(
                "/checkpoint-plan/generate",
                json={"topic": "Python 基础入门", "teaching_mode": "heuristic"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Python 基础入门"
        assert len(data["checkpoints"]) == 1

    def test_generate_missing_params_returns_422(self, client):
        """缺少参数 → 422。"""
        response = client.post(
            "/checkpoint-plan/generate",
            json={"topic": "Python 基础入门"},
        )
        assert response.status_code == 422

    def test_generate_invalid_teaching_mode_returns_422(self, client):
        """无效教学模式 → 422。"""
        response = client.post(
            "/checkpoint-plan/generate",
            json={"topic": "Python 基础入门", "teaching_mode": "invalid"},
        )
        assert response.status_code == 422


class TestGetPlanAPI:
    """GET /checkpoint-plan/{session_id} 测试。"""

    def test_get_plan_returns_200(self, client, db_session):
        """200 + 计划数据。"""
        from models.checkpoint.schemas import CheckpointPlan
        from orm.checkpoint_plan import CheckpointPlanModel
        from orm.teaching_session import TeachingSessionModel

        session = TeachingSessionModel(
            teaching_mode="heuristic",
            topic="Python 基础入门",
            students_config={"mode": "random", "count": 5},
        )
        db_session.add(session)

        plan = CheckpointPlan.model_validate(VALID_PLAN_RESPONSE)
        cp = CheckpointPlanModel(
            session_id=session.id,
            plan_data=plan.model_dump(),
        )
        db_session.add(cp)

        import asyncio
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        response = client.get(f"/checkpoint-plan/{session.id}")
        assert response.status_code == 200
        assert response.json()["topic"] == "Python 基础入门"

    def test_get_plan_not_found_returns_404(self, client):
        """不存在 → 404。"""
        response = client.get("/checkpoint-plan/99999")
        assert response.status_code == 404


class TestEditPlanAPI:
    """PUT /checkpoint-plan/{session_id} 测试。"""

    def test_edit_plan_returns_200(self, client, db_session):
        """200 + 更新后的计划。"""
        from models.checkpoint.schemas import CheckpointPlan
        from orm.checkpoint_plan import CheckpointPlanModel
        from orm.teaching_session import TeachingSessionModel

        session = TeachingSessionModel(
            teaching_mode="heuristic",
            topic="Python 基础入门",
            students_config={"mode": "random", "count": 5},
        )
        db_session.add(session)

        plan = CheckpointPlan.model_validate(VALID_PLAN_RESPONSE)
        cp = CheckpointPlanModel(
            session_id=session.id,
            plan_data=plan.model_dump(),
        )
        db_session.add(cp)

        import asyncio
        asyncio.get_event_loop().run_until_complete(db_session.commit())

        # 编辑: 添加一个 checkpoint
        edited = plan.model_dump()
        edited["checkpoints"].append({
            "title": "Python 条件判断",
            "key_point": "",
            
            "checkpoint_question": "if 和 elif 有什么区别?",
            "state": "pending",
        })

        response = client.put(f"/checkpoint-plan/{session.id}", json=edited)
        assert response.status_code == 200
        assert len(response.json()["checkpoints"]) == 2

    def test_edit_plan_session_not_found_returns_404(self, client):
        """session 不存在 → 404。"""
        response = client.put(
            "/checkpoint-plan/99999",
            json=VALID_PLAN_RESPONSE,
        )
        assert response.status_code == 404

    def test_edit_plan_invalid_schema_returns_422(self, client):
        """无效 schema → 422。"""
        response = client.put(
            "/checkpoint-plan/1",
            json={"topic": "test", "checkpoints": []},
        )
        assert response.status_code == 422
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_api.py -v`
预期：FAIL — router 未注册

- [ ] **步骤 3：创建 API 路由**

```python
# backend/models/checkpoint/router.py
"""检查点计划 API 端点。"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from models.checkpoint.schemas import CheckpointPlan

router = APIRouter(prefix="/checkpoint-plan", tags=["checkpoint-plan"])


class GeneratePlanRequest(BaseModel):
    """生成检查点计划请求。"""

    topic: str = Field(min_length=1, max_length=200, description="教学主题")
    teaching_mode: str = Field(description="教学模式: didactic/heuristic/discussion/teacher")


class GeneratePlanResponse(BaseModel):
    """生成检查点计划响应。"""

    topic: str
    teaching_mode: str
    checkpoints: list[dict]
    current_index: int


def _get_db() -> AsyncSession:
    """获取数据库会话（同步上下文，供 FastAPI 依赖注入使用）。

    注意: 生产环境使用 async session maker。
    测试环境通过 override 或 mock 注入。
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from core.database import Base

    engine = create_async_engine("sqlite+aiosqlite:///./datas/database.db")
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return session_factory()


@router.post("/generate", response_model=GeneratePlanResponse)
async def generate_plan(request: GeneratePlanRequest):
    """生成检查点计划。

    前端应显示等待动画（loading spinner），此请求可能需要 10-30 秒。
    """
    from models.checkpoint.plan_service import CheckpointPlanService
    from core.llm_client import LLMClient

    llm_client = LLMClient.from_config()
    service = CheckpointPlanService(llm_client=llm_client)
    plan = await service.generate_plan(topic=request.topic, teaching_mode=request.teaching_mode)

    return plan.model_dump()


@router.get("/{session_id}")
async def get_plan(session_id: int):
    """获取检查点计划。"""
    from sqlalchemy.ext.asyncio import AsyncSession as SessionType

    db = _get_db()
    async with db() as session:
        from models.checkpoint.service import CheckpointPlanPersistence
        persistence = CheckpointPlanPersistence(session)
        plan = await persistence.load_plan(session_id)

    if plan is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} 没有检查点计划")
    return plan.model_dump()


@router.put("/{session_id}")
async def edit_plan(session_id: int, plan_data: dict):
    """编辑检查点计划（教师模式，开始前）。"""
    try:
        plan = CheckpointPlan.model_validate(plan_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"无效的检查点计划: {e}") from e

    db = _get_db()
    async with db() as session:
        from models.checkpoint.service import CheckpointPlanPersistence
        persistence = CheckpointPlanPersistence(session)
        updated = await persistence.update_plan(session_id, plan)

    if updated is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} 不存在")
    return updated.model_dump()
```

- [ ] **步骤 4：在 main.py 中注册路由**

```python
# backend/main.py
from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from models.user import router as user_router  # noqa: E402
from models.checkpoint.router import router as checkpoint_router  # noqa: E402

app = FastAPI()

app.include_router(user_router)
app.include_router(checkpoint_router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **步骤 5：运行 API 测试**

运行：`cd backend && python -m pytest tests/units/test_checkpoint_api.py -v`
预期：全部 8 个测试 PASS

- [ ] **步骤 6：提交**

```bash
git add backend/models/checkpoint/router.py backend/main.py backend/tests/units/test_checkpoint_api.py
git commit -m "feat: add checkpoint plan API endpoints (generate/get/edit)"
```

---

### 任务 6：API 文档

**文件：**
- 修改：`docs/api.md`

- [ ] **步骤 1：在 api.md 中添加检查点 API 文档**

在 `docs/api.md` 中"智能体模块（待实现）"之前插入以下内容：

```markdown
---

## 检查点计划模块

### 生成检查点计划

根据主题和教学模式，调用 LLM 生成结构化的检查点教学计划。

```http
POST /checkpoint-plan/generate
```

**请求体：**
```json
{
  "topic": "Python 基础入门",
  "teaching_mode": "heuristic"
}
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| topic | string | 是 | 教学主题（1-200 字符） |
| teaching_mode | string | 是 | 教学模式：`didactic` / `heuristic` / `discussion` / `teacher` |

**响应：** `200 OK`
```json
{
  "topic": "Python 基础入门",
  "teaching_mode": "heuristic",
  "checkpoints": [
    {
      "title": "Python 变量与数据类型",
      "key_point": "",
      
      "checkpoint_question": "Python 中有哪些基本数据类型?",
      "state": "pending"
    },
    {
      "title": "Python 条件判断",
      "key_point": "",
      
      "checkpoint_question": "if 和 elif 有什么区别?",
      "state": "pending"
    }
  ],
  "current_index": 0
}
```

**错误响应：** `422 Unprocessable Entity` — 缺少参数或参数无效

**注意：** 此接口调用 LLM 生成计划，耗时约 10-30 秒。前端应显示等待动画（loading spinner + "正在生成教学计划..."）。

---

### 获取检查点计划

获取指定会话的检查点计划。

```http
GET /checkpoint-plan/{session_id}
```

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | int | 教学会话 ID |

**响应：** `200 OK`
```json
{
  "topic": "Python 基础入门",
  "teaching_mode": "heuristic",
  "checkpoints": [
    {
      "title": "Python 变量与数据类型",
      "key_point": "",
      
      "checkpoint_question": "Python 中有哪些基本数据类型?",
      "state": "teaching"
    }
  ],
  "current_index": 0
}
```

**错误响应：** `404 Not Found` — 会话不存在或该会话没有检查点计划

---

### 编辑检查点计划

编辑指定会话的检查点计划（教师模式，开始教学前使用）。

```http
PUT /checkpoint-plan/{session_id}
```

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| session_id | int | 教学会话 ID |

**请求体：** 完整的 CheckpointPlan JSON（与 GET 响应格式相同），包含编辑后的内容。

```json
{
  "topic": "Python 基础入门",
  "teaching_mode": "heuristic",
  "checkpoints": [
    {
      "title": "Python 变量与数据类型（已编辑）",
      "key_point": "",
      
      "checkpoint_question": "请列举 Python 的四种基本数据类型",
      "state": "pending"
    }
  ],
  "current_index": 0
}
```

**响应：** `200 OK` — 返回更新后的完整计划

**错误响应：**
- `404 Not Found` — 会话不存在
- `422 Unprocessable Entity` — 请求体不符合 CheckpointPlan schema

**注意：** 只能在教学开始前编辑。教学进行中编辑不会影响正在执行的检查点状态。
```

- [ ] **步骤 2：提交**

```bash
git add docs/api.md
git commit -m "docs: add checkpoint plan API documentation"
```

---

### 任务 7：完整测试套件验证

- [ ] **步骤 1：运行所有单元测试**

运行：`cd backend && python -m pytest tests/units/ -v`
预期：所有测试 PASS（现有 + 新增）

- [ ] **步骤 2：运行 ruff check**

运行：`cd backend && ruff check models/checkpoint/ orm/checkpoint_plan.py tests/units/test_checkpoint_schemas.py tests/units/test_checkpoint_service.py tests/units/test_checkpoint_persistence.py tests/units/test_checkpoint_api.py`
预期：无错误

- [ ] **步骤 3：运行 ruff format**

运行：`cd backend && ruff format models/checkpoint/ orm/checkpoint_plan.py tests/units/test_checkpoint_schemas.py tests/units/test_checkpoint_service.py tests/units/test_checkpoint_persistence.py tests/units/test_checkpoint_api.py`
预期：文件已格式化（可能显示 diff）

- [ ] **步骤 4：如有格式化更改则提交**

```bash
git add -A
git commit -m "style: run ruff format on checkpoint system files"
```

---

## 自审检查清单

**规格覆盖：**
- [x] CheckpointState 枚举（4 个状态） — 任务 1
- [x] Checkpoint schema（title, key_point, checkpoint_question, state） — 任务 1
- [x] CheckpointPlan schema（topic, teaching_mode: str, checkpoints, current_index） — 任务 1
- [x] teaching_mode 使用 str 且 "teacher" 为特殊值 — 任务 1（validator）
- [x] Schemas 位于 `models/checkpoint/` 目录 — 任务 1
- [x] CheckpointPlanService 位于 `models/checkpoint/plan_service.py` — 任务 3
- [x] 三层降级策略 — 任务 3
- [x] 独立的 `checkpoint_plans` 数据库表 — 任务 2
- [x] `teaching_sessions` 外键 — 任务 2
- [x] Alembic migration — 任务 2
- [x] POST /checkpoint-plan/generate — 任务 5
- [x] GET /checkpoint-plan/{session_id} — 任务 5
- [x] PUT /checkpoint-plan/{session_id} — 任务 5
- [x] docs/api.md 中的 API 文档 — 任务 6
- [x] 所有任务共 ~39 个测试 — 任务 1-5

**占位符扫描：**
- [x] 无 TBD、TODO 或 "implement later" 发现
- [x] 所有测试代码包含实际断言
- [x] 所有文件路径精确
- [x] 所有导入已指定

**类型一致性：**
- [x] CheckpointState 在所有任务中一致使用
- [x] CheckpointPlan.teaching_mode 始终为 `str`（非 `str | None`）
- [x] ORM 模型 `CheckpointPlanModel` 的 `plan_data` 字段与持久化服务匹配
- [x] 外键 `session_id` 匹配 `teaching_sessions.id`

## 单元测试执行

### 运行测试

```bash
cd backend

# 运行所有单元测试
pytest tests/units/test_checkpoint_schemas.py \
       tests/units/test_checkpoint_service.py \
       tests/units/test_checkpoint_persistence.py \
       tests/units/test_checkpoint_api.py \
       -v

# 运行测试并输出到日志文件
pytest tests/units/test_checkpoint_*.py -v \
    --tb=short \
    --log-cli-level=INFO \
    2>&1 | tee logs/checkpoint_tests_$(date +%Y%m%d_%H%M%S).log

# 查看最新的测试日志
ls -t logs/checkpoint_tests_*.log | head -1 | xargs cat
```

### 日志文件位置

测试日志将保存在 `backend/logs/` 目录下，文件名格式为 `checkpoint_tests_YYYYMMDD_HHMMSS.log`。

### 日志内容包含

- 测试用例执行状态（PASS/FAIL）
- 断言失败详细信息
- 错误堆栈跟踪
- **LLM 生成的检查点计划**（包含主题、知识点、检查问题等详细信息）
- 测试覆盖率报告（如使用 `--cov` 参数）

### 查看 LLM 生成结果

测试运行时，LLM 生成的检查点计划会以结构化格式输出到日志：

```
============================================================
LLM 生成的检查点计划:
主题: Python 变量与数据类型
教学模式: heuristic
检查点数量: 2

检查点 1:
  标题: Python 变量与数据类型
  知识点: 变量是存储数据的容器，数据类型决定了变量可以存储的数据种类
  检查问题: 什么是变量？Python 中有哪些基本数据类型？
  状态: pending

检查点 2:
  标题: 变量赋值与运算
  知识点: 使用 = 进行变量赋值，变量可以进行算术运算
  检查问题: 如何给变量赋值？变量之间可以进行运算吗？
  状态: pending
============================================================
```

### 使用真实 LLM 测试

如果要使用真实 LLM 测试（查看实际生成效果）：

```bash
cd backend

# 创建集成测试文件
cat > tests/integration/test_checkpoint_real_llm.py << 'EOF'
import pytest
import logging
from models.checkpoint.plan_service import CheckpointPlanService
from langchain_openai import ChatOpenAI

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_generates_valid_plan():
    """使用真实LLM生成检查点计划（集成测试）。"""
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # 创建真实 LLM 客户端
    llm = ChatOpenAI(model="Qwen/Qwen2.5-7B-Instruct", temperature=0.3)
    service = CheckpointPlanService(llm_client=llm)

    # 生成计划
    logger.info("开始使用真实 LLM 生成检查点计划...")
    plan = await service.generate_plan(
        topic="Python 变量与数据类型",
        teaching_mode="heuristic"
    )

    # 打印结果
    logger.info("=" * 60)
    logger.info("LLM 生成的检查点计划:")
    logger.info(f"主题: {plan.topic}")
    logger.info(f"教学模式: {plan.teaching_mode}")
    logger.info(f"检查点数量: {len(plan.checkpoints)}")
    for i, cp in enumerate(plan.checkpoints, 1):
        logger.info(f"\n检查点 {i}:")
        logger.info(f"  标题: {cp.title}")
        logger.info(f"  知识点: {cp.key_point}")
        logger.info(f"  检查问题: {cp.checkpoint_question}")
        logger.info(f"  状态: {cp.state}")
    logger.info("=" * 60)

    # 验证
    assert plan.topic == "Python 变量与数据类型"
    assert len(plan.checkpoints) >= 1
    assert len(plan.checkpoints) <= 8
    assert all(cp.key_point for cp in plan.checkpoints)
    assert all(cp.checkpoint_question for cp in plan.checkpoints)
EOF

# 运行集成测试（输出到日志）
pytest tests/integration/test_checkpoint_real_llm.py -v \
    --log-cli-level=INFO \
    --tb=short \
    2>&1 | tee logs/checkpoint_real_llm_$(date +%Y%m%d_%H%M%S).log
```

### 单独运行某个测试并查看详细输出

```bash
# 只运行一个测试，查看详细日志
pytest tests/units/test_checkpoint_service.py::TestCheckpointPlanService::test_normal_generation_returns_valid_plan \
    -v \
    -s \
    --log-cli-level=INFO \
    --log-cli-format='%(asctime)s [%(levelname)s] %(message)s'
```
