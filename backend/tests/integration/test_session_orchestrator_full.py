"""SessionOrchestrator 完整流程集成测试.

包含两种测试：
1. mock LLM 版本 - 快速验证流程逻辑
2. 真实 LLM 版本 - 展示完整课堂过程（带控制台输出）
"""

import asyncio  # noqa: E402

import pytest  # noqa: E402

from models.checkpoint.schemas import CheckpointState  # noqa: E402


def test_acceptance_criteria():
    """验收标准：能自动运行完整教学流程."""
    import asyncio
    from unittest.mock import Mock

    from agents.memories import SessionMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.student_agent import StudentAgent
    from agents.teacher_agent import TeacherAgent
    from models.checkpoint.schemas import Checkpoint, CheckpointPlan
    from models.session.orchestrator import SessionOrchestrator
    from schemas.message import MessageType
    from schemas.student import StudentAttitude, StudentLevel, StudentProfile

    async def test():
        # Mock LLM
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="Test content")

        session_memory = SessionMemory(session_id=1, topic="Test")
        memory_manager = MemoryManager(session_memory=session_memory)

        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=memory_manager,
        )

        student = StudentAgent(
            session_memory=session_memory,
            llm=mock_llm,
            profile=StudentProfile(
                name="S1",
                level=StudentLevel.AVERAGE,
                attitude=StudentAttitude.NEUTRAL,
                learning_ability=5,
            ),
            rng=Mock(random=Mock(return_value=0.1)),  # Low response rate
        )

        plan = CheckpointPlan(
            topic="Test",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(title="CP1", key_point="P1", checkpoint_question="Q1?"),
                Checkpoint(title="CP2", key_point="P2", checkpoint_question="Q2?"),
            ],
        )

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager,
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
            msg
            for msg in session_memory.message_history
            if hasattr(msg, "message_type") and msg.message_type == MessageType.ASSIGN_HOMEWORK
        ]
        assert len(hw_messages) > 0

    asyncio.run(test())


def test_full_observation_session():
    """测试完整的观察模式会话流程 (使用 mock LLM)."""
    from unittest.mock import Mock

    from agents.memories import SessionMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.student_agent import StudentAgent
    from agents.teacher_agent import TeacherAgent
    from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
    from models.session.orchestrator import SessionOrchestrator
    from schemas.student import StudentAttitude, StudentLevel, StudentProfile

    async def test():
        # Mock LLM - make invoke return actual string
        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="Test response")

        # 创建 session
        session_memory = SessionMemory(session_id=1, topic="Python Basics")
        memory_manager = MemoryManager(session_memory=session_memory)

        # 创建 teacher
        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=mock_llm,
            teaching_mode="heuristic",
            memory_manager=memory_manager,
        )

        # 创建学生
        student_profile = StudentProfile(
            name="TestStudent",
            level=StudentLevel.AVERAGE,
            attitude=StudentAttitude.ACTIVE,
            learning_ability=5,
        )

        # Mock student's rng to make should_respond() return True
        student = StudentAgent(
            session_memory=session_memory,
            llm=mock_llm,
            profile=student_profile,
            rng=Mock(random=Mock(return_value=0.9)),  # Always respond
        )

        # 创建检查点计划（2个检查点）
        plan = CheckpointPlan(
            topic="Python Basics",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="Variables",
                    key_point="Python variables store data",
                    checkpoint_question="What is a variable?",
                ),
                Checkpoint(
                    title="Data Types",
                    key_point="Python has several data types",
                    checkpoint_question="Name some Python data types.",
                ),
            ],
        )

        # 创建 orchestrator
        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager,
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
        assert len(session_memory.message_history) > 0

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

    from agents.memories import SessionMemory, StudentAgentMemory, TeacherAgentMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.student_agent import StudentAgent
    from agents.teacher_agent import TeacherAgent
    from core.llm_client import LLMClient
    from models.checkpoint.service import CheckpointPlanService
    from models.session.orchestrator import SessionOrchestrator
    from schemas.student import StudentAttitude, StudentLevel, StudentProfile

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
            ("张三", StudentLevel.EXCELLENT, StudentAttitude.ACTIVE, 8),
            ("李四", StudentLevel.AVERAGE, StudentAttitude.NEUTRAL, 5),
            ("王五", StudentLevel.BASIC, StudentAttitude.PASSIVE, 3),
        ]

        for name, level, attitude, learning_ability in student_configs:
            profile = StudentProfile(
                name=name, level=level, attitude=attitude, learning_ability=learning_ability
            )
            student_memory = StudentAgentMemory.from_profile(profile)
            student = StudentAgent(
                session_memory=session_memory, llm=llm, profile=profile, memory=student_memory
            )
            students.append(student)

        # 创建教师
        teacher = TeacherAgent(
            session_memory=session_memory, llm=llm, teaching_mode="heuristic"
        )

        # 创建 MemoryManager
        memory_manager = MemoryManager(session_memory=session_memory)
        memory_manager.teacher_memory = teacher_memory
        for student in students:
            memory_manager.student_memories[student.profile.name] = student.memory

        # 生成检查点计划（使用真实 LLM）
        print(f"\n{'=' * 70}")
        print("【观察模式集成测试】主题: Python 变量基础")
        print("教学模式: 启发式 (heuristic)")
        print(f"学生数量: {len(students)}")
        print(f"{'=' * 70}\n")

        checkpoint_service = CheckpointPlanService(llm=llm)
        plan = await checkpoint_service.generate_plan(
            topic="Python 变量基础", teaching_mode="heuristic", checkpoint_count=2
        )

        print("生成的检查点计划:")
        print(f"  主题: {plan.topic}")
        print(f"  教学模式: {plan.teaching_mode}")
        print(f"  检查点数量: {len(plan.checkpoints)}")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"    检查点 {i}: {cp.title}")
        print(f"\n{'=' * 70}")
        print("【开始上课】")
        print(f"{'=' * 70}\n")

        # 创建 orchestrator
        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=students,
            checkpoint_plan=plan,
            memory_manager=memory_manager,
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
        print("【课程结束】")
        print(f"{'=' * 70}")

        # 打印课程统计
        print("\n课程统计:")
        print(f"  总消息数: {len(session_memory.message_history)}")
        print(f"  教师讲授主题: {len(teacher_memory.covered_topics)}")
        print("  学生参与情况:")
        for student in students:
            participation = teacher_memory.student_participation.get(student.profile.name, 0)
            print(f"    {student.profile.name}: {participation} 次参与")

        # 打印最后几条消息
        print("\n最后几条消息:")
        for msg in session_memory.message_history[-5:]:
            sender = msg.sender
            msg_type = msg.message_type.value
            content = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
            print(f"  [{sender}] ({msg_type}): {content}")

        print(f"\n{'=' * 70}\n")

        # 验证
        assert len(session_memory.message_history) > 0
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

    from agents.memories import SessionMemory, StudentAgentMemory, TeacherAgentMemory
    from agents.memories.memory_manager import MemoryManager
    from agents.student_agent import StudentAgent
    from agents.teacher_agent import TeacherAgent
    from core.llm_client import LLMClient
    from models.checkpoint.service import CheckpointPlanService
    from models.session.orchestrator import SessionOrchestrator
    from schemas.student import StudentAttitude, StudentLevel, StudentProfile

    async def test():
        llm = LLMClient.from_config()

        # 创建 session
        session_id = 8888
        session_memory = SessionMemory(session_id=session_id, topic="Python 条件语句与循环")
        teacher_memory = TeacherAgentMemory()

        # 创建 5 个学生，模拟真实课堂的多样性
        student_configs = [
            ("赵学霸", StudentLevel.EXCELLENT, StudentAttitude.ACTIVE, 9),
            ("钱积极", StudentLevel.AVERAGE, StudentAttitude.ACTIVE, 7),
            ("孙普通", StudentLevel.AVERAGE, StudentAttitude.NEUTRAL, 5),
            ("李沉默", StudentLevel.AVERAGE, StudentAttitude.PASSIVE, 4),
            ("周小白", StudentLevel.BASIC, StudentAttitude.PASSIVE, 3),
        ]

        students = []
        for name, level, attitude, learning_ability in student_configs:
            profile = StudentProfile(
                name=name, level=level, attitude=attitude, learning_ability=learning_ability
            )
            student_memory = StudentAgentMemory.from_profile(profile)
            student = StudentAgent(
                session_memory=session_memory, llm=llm, profile=profile, memory=student_memory
            )
            students.append(student)

        # 创建教师
        teacher = TeacherAgent(
            session_memory=session_memory, llm=llm, teaching_mode="heuristic"
        )

        # 创建 MemoryManager
        memory_manager = MemoryManager(session_memory=session_memory)
        memory_manager.teacher_memory = teacher_memory
        for student in students:
            memory_manager.student_memories[student.profile.name] = student.memory

        # 打印课堂信息
        print(f"\n{'#' * 70}")
        print("  多学生课堂集成测试")
        print(f"{'#' * 70}")
        print(f"  主题: {session_memory.topic}")
        print("  教学模式: 启发式 (heuristic)")
        print("  学生列表:")
        for s in students:
            level_str = s.profile.level.value
            attitude_str = s.profile.attitude.value
            print(f"    - {s.profile.name} (水平: {level_str}, 态度: {attitude_str})")
        print(f"{'#' * 70}\n")

        # 生成检查点计划（3 个检查点）
        print("[1/4] 生成检查点计划...")
        checkpoint_service = CheckpointPlanService(llm=llm)
        plan = await checkpoint_service.generate_plan(
            topic=session_memory.topic, teaching_mode="heuristic", checkpoint_count=3
        )

        print(f"[2/4] 检查点计划生成完成，共 {len(plan.checkpoints)} 个检查点\n")

        # 创建 orchestrator
        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=students,
            checkpoint_plan=plan,
            memory_manager=memory_manager,
        )

        # 运行会话
        print("[3/4] 开始上课...\n")
        await orchestrator.run_autonomous_session()

        print("\n[4/4] 课程完成！\n")

        # 打印统计
        print(f"\n{'=' * 60}")
        print("  课堂统计")
        print(f"{'=' * 60}")
        print(f"  总消息数: {len(session_memory.message_history)}")
        print(f"  教师讲授主题: {len(teacher_memory.covered_topics)}")
        print("  学生参与情况:")
        for student in students:
            participation = teacher_memory.student_participation.get(student.profile.name, 0)
            learned = len(student.memory.knowledge_points)
            print(f"    {student.profile.name}: {participation} 次参与, 学会 {learned} 个知识点")
        print(f"{'=' * 60}\n")

        # 验证
        assert len(session_memory.message_history) > 0
        for cp in plan.checkpoints:
            assert cp.state == CheckpointState.COMPLETE

    asyncio.run(test())
