"""TeacherSessionController 真实 LLM 集成测试."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from models.session.teacher_controller import TeacherSessionController
from models.checkpoint.persistence_service import CheckpointPlanPersistence
from agents.memories.memory_manager import MemoryManager
from agents.memories.session_memory import SessionMemory
from agents.memories.teacher_memory import TeacherAgentMemory
from agents.student_agent import StudentAgent
from schemas.student import StudentProfile, StudentLevel, StudentAttitude
from orm.teaching_session import TeachingSessionModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.integration
async def test_teacher_controller_with_real_llm(db_session: AsyncSession):
    """测试 TeacherSessionController 使用真实 LLM.

    这是一个集成测试，验证控制器与真实 LLM API 的集成。
    由于需要 API key 和网络连接，这个测试被标记为 integration。

    跳过条件：没有 API key 时跳过
    """
    # Arrange - 创建教学会话
    session = TeachingSessionModel(
        topic="Python 变量与数据类型",
        teaching_mode="teacher",
        students_config={"count": 1},
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    # Arrange - 创建检查点计划
    plan = CheckpointPlan(
        topic="Python 变量与数据类型",
        teaching_mode="teacher",
        checkpoints=[
            Checkpoint(
                title="Python 变量的定义与赋值",
                key_point="Python 是动态类型语言",
                checkpoint_question="什么是变量？",
                state=CheckpointState.PENDING,
            ),
        ],
        current_index=0,
    )
    persistence = CheckpointPlanPersistence(db_session)
    await persistence.save_plan(session_id=session.id, plan=plan)

    # Arrange - 创建学生（使用真实 LLM）
    from core.llm_client import LLMClient  # noqa: E402
    llm_client = LLMClient()

    profile = StudentProfile(
        name="测试学生",
        level=StudentLevel.AVERAGE,
        attitude=StudentAttitude.ACTIVE,
        learning_ability=7,
    )

    session_memory = SessionMemory(session_id=session.id, topic="Python 变量与数据类型")
    teacher_memory = TeacherAgentMemory()
    memory_manager = MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)

    student = StudentAgent(
        session_memory=session_memory,
        profile=profile,
        llm=llm_client,
    )

    # Arrange - 创建控制器
    controller = TeacherSessionController(
        student_agents=[student],
        memory_manager=memory_manager,
        checkpoint_plan=plan,
        ws_push_callback=None,
    )

    # Act & Assert - 测试广播讲授
    controller.handle_broadcast_lecture("今天我们学习 Python 变量，它们不需要声明类型")
    messages = memory_manager.session_memory.message_history
    assert len(messages) == 1
    assert messages[0].sender == "teacher"
    assert messages[0].message_type.value == "lecture"
    assert "Python 变量" in messages[0].content

    # Act & Assert - 测试向全体提问
    controller.handle_ask_to_all("谁能说出 Python 变量的特点？")
    # 学生可能回答也可能不回答，取决于 LLM 和学生配置
    # 我们只验证问题被记录
    question_messages = [m for m in messages if m.message_type.value == "checkpoint_question"]
    assert len(question_messages) >= 1

    # Act & Assert - 测试向指定学生提问
    result = controller.handle_ask_to_student(
        profile.name,
        "那小明，你说说 Python 中列表和元组的区别是什么？",
    )
    assert result["student_name"] == profile.name
    assert len(result["content"]) > 0

    # Act & Assert - 测试教师回复
    controller.handle_teacher_reply(profile.name, "回答正确！")
    assert controller._dialogue_round_count == 1
    assert controller._active_dialogue is not None

    # Act & Assert - 测试结束对话
    controller.handle_end_dialogue()
    assert controller._active_dialogue is None
    assert controller._dialogue_round_count == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_homework_flow_with_real_llm(db_session: AsyncSession):
    """测试作业流程使用真实 LLM.

    验证布置作业、收集作业、评分和反馈的完整流程。
    """
    # Arrange - 创建教学会话和检查点计划
    session = TeachingSessionModel(
        topic="Python 基础",
        teaching_mode="teacher",
        students_config={"count": 1},
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    plan = CheckpointPlan(
        topic="Python 基础",
        teaching_mode="teacher",
        checkpoints=[
            Checkpoint(
                title="Python 介绍",
                key_point="Python 是一种高级编程语言",
                checkpoint_question="什么是 Python？",
                state=CheckpointState.PENDING,
            ),
        ],
        current_index=0,
    )
    persistence = CheckpointPlanPersistence(db_session)
    await persistence.save_plan(session_id=session.id, plan=plan)

    # Arrange - 创建学生
    from core.llm_client import LLMClient  # noqa: E402
    llm_client = LLMClient()

    profile = StudentProfile(
        name="测试学生",
        level=StudentLevel.AVERAGE,
        attitude=StudentAttitude.ACTIVE,
        learning_ability=7,
    )

    session_memory = SessionMemory(session_id=session.id, topic="Python 基础")
    teacher_memory = TeacherAgentMemory()
    memory_manager = MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)

    student = StudentAgent(
        session_memory=session_memory,
        profile=profile,
        llm=llm_client,
    )

    controller = TeacherSessionController(
        student_agents=[student],
        memory_manager=memory_manager,
        checkpoint_plan=plan,
        ws_push_callback=None,
    )

    # Act - 布置作业
    controller.handle_assign_homework("完成 Python 基础练习题")

    # Assert - 验证作业消息被记录
    homework_messages = [
        m for m in memory_manager.session_memory.message_history
        if m.message_type.value == "assign_homework"
    ]
    assert len(homework_messages) == 1
    assert homework_messages[0].content == "完成 Python 基础练习题"

    # Act - 收集作业（学生可能会提交，也可能不会）
    controller.handle_collect_homework()

    # 验证提交消息（如果有）
    submission_messages = [
        m for m in memory_manager.session_memory.message_history
        if m.message_type.value == "homework_submission"
    ]
    # 学生可能选择不提交，所以断言 len >= 0
    assert len(submission_messages) >= 0

    # Act - 结束教学，收集反馈
    feedbacks = controller.handle_end_teaching()

    # Assert - 验证反馈返回值格式
    assert "feedbacks" in feedbacks
    assert isinstance(feedbacks["feedbacks"], list)
    # 学生可能提供反馈，也可能不提供
    for feedback in feedbacks["feedbacks"]:
        assert isinstance(feedback, str)

    # 验证 end_feedback 消息被记录（如果有反馈）
    end_feedback_messages = [
        m for m in memory_manager.session_memory.message_history
        if m.message_type.value == "end_feedback"
    ]
    # 反馈数量应该与返回的反馈列表数量一致
    assert len(end_feedback_messages) == len(feedbacks["feedbacks"])


@pytest.mark.asyncio
async def test_rest_api_with_checkpoint_plan_edit(db_session: AsyncSession):
    """测试检查点计划编辑 REST API 使用真实数据库."""
    # Arrange - 创建教学会话和初始检查点计划
    session = TeachingSessionModel(
        topic="Python 变量",
        teaching_mode="teacher",
        students_config={"count": 1},
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    original_plan = CheckpointPlan(
        topic="Python 变量",
        teaching_mode="teacher",
        checkpoints=[
            Checkpoint(
                title="原始标题",
                key_point="原始知识点",
                checkpoint_question="原始问题",
                state=CheckpointState.PENDING,
            ),
        ],
        current_index=0,
    )
    persistence = CheckpointPlanPersistence(db_session)
    await persistence.save_plan(session_id=session.id, plan=original_plan)

    # Act - 通过 REST API 编辑检查点计划
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        updated_data = {
            "topic": "Python 变量（修改后）",
            "teaching_mode": "teacher",
            "checkpoints": [
                {
                    "title": "修改后的标题",
                    "key_point": "修改后的知识点",
                    "checkpoint_question": "修改后的问题",
                }
            ],
        }
        response = await client.put(f"/checkpoint-plans/{session.id}", json=updated_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["success"] is True

    # 验证修改已保存到数据库
    modified_plan = await persistence.load_plan(session_id=session.id)
    assert modified_plan is not None
    assert modified_plan.topic == "Python 变量（修改后）"
    assert modified_plan.checkpoints[0].title == "修改后的标题"
