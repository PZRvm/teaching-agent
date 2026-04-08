"""LLM 讲授内容 → WebSocket 实时推送集成测试（真实 LLM）.

验证链路: 真实 LLM → TeacherAgent.deliver_lecture() → SessionOrchestrator._teach_checkpoint()
→ _ws_push_checkpoint_state() → ws_push_callback 收到 checkpoint_state_change 事件

运行方式:
    pytest tests/integration_llm/test_websocket_llm_push.py -v -s -m integration
"""

import asyncio
from unittest.mock import Mock

import pytest


@pytest.mark.integration
def test_teach_checkpoint_ws_push_didactic():
    """测试: didactic 模式下，LLM 讲授后 ws_push_callback 收到 teaching → complete 事件."""
    from dotenv import load_dotenv

    load_dotenv()

    async def _test():
        from agents.memories.memory_manager import MemoryManager
        from agents.memories.session_memory import SessionMemory
        from agents.student_agent import StudentAgent
        from agents.teacher_agent import TeacherAgent
        from core.llm_client import LLMClient
        from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
        from models.session.orchestrator import SessionOrchestrator
        from schemas.student import StudentAttitude, StudentLevel, StudentProfile

        llm = LLMClient.from_config()

        session_memory = SessionMemory(session_id=42, topic="Python 变量基础")
        memory_manager = MemoryManager(session_memory=session_memory)

        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=llm,
            teaching_mode="didactic",
            memory_manager=memory_manager,
        )

        student = StudentAgent(
            session_memory=session_memory,
            llm=llm,
            profile=StudentProfile(
                name="测试学生",
                level=StudentLevel.AVERAGE,
                attitude=StudentAttitude.NEUTRAL,
                learning_ability=5,
            ),
        )

        checkpoint = Checkpoint(
            title="变量基础",
            key_point="变量的定义和赋值",
            checkpoint_question="什么是变量？",
        )
        plan = CheckpointPlan(
            topic="Python 变量基础",
            teaching_mode="didactic",
            checkpoints=[checkpoint],
        )

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager,
        )

        # 收集 WebSocket 推送消息
        ws_messages = []

        async def ws_callback(msg):
            ws_messages.append(msg)
            data = msg["data"]
            cp = data["checkpoint"]
            print(f"\n[WebSocket 推送] type={msg['type']}, state={cp['state']}, title={cp['title']}")

        orchestrator.set_ws_push_callback(ws_callback)

        # 执行 _teach_checkpoint
        print(f"\n{'=' * 60}")
        print("开始讲授检查点: 变量基础")
        print(f"{'=' * 60}")
        await orchestrator._teach_checkpoint(checkpoint)

        # 打印 LLM 讲授内容
        lecture_msgs = [
            m for m in session_memory.message_history
            if m.message_type.value == "lecture"
        ]
        print("\n[LLM 讲授内容]:")
        print(f"{'-' * 60}")
        for msg in lecture_msgs:
            print(f"  {msg.content}")
        print(f"{'-' * 60}")

        # 验证 WebSocket 推送
        state_change_msgs = [
            msg for msg in ws_messages if msg["type"] == "checkpoint_state_change"
        ]
        assert len(state_change_msgs) == 2
        assert state_change_msgs[0]["data"]["checkpoint"]["state"] == "teaching"
        assert state_change_msgs[1]["data"]["checkpoint"]["state"] == "complete"
        assert checkpoint.state == CheckpointState.COMPLETE

        print(f"\n验证通过: 收到 {len(state_change_msgs)} 个 WebSocket 推送事件")

    asyncio.run(_test())


@pytest.mark.integration
def test_teach_checkpoint_ws_push_heuristic():
    """测试: heuristic 模式下，LLM 讲授+提问后 ws_push_callback 收到 teaching → questions → complete."""
    from dotenv import load_dotenv

    load_dotenv()

    async def _test():
        from agents.memories.memory_manager import MemoryManager
        from agents.memories.session_memory import SessionMemory
        from agents.student_agent import StudentAgent
        from agents.teacher_agent import TeacherAgent
        from core.llm_client import LLMClient
        from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
        from models.session.orchestrator import SessionOrchestrator
        from schemas.student import StudentAttitude, StudentLevel, StudentProfile

        llm = LLMClient.from_config()

        session_memory = SessionMemory(session_id=43, topic="Python 条件语句")
        memory_manager = MemoryManager(session_memory=session_memory)

        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=llm,
            teaching_mode="heuristic",
            memory_manager=memory_manager,
        )

        student = StudentAgent(
            session_memory=session_memory,
            llm=llm,
            profile=StudentProfile(
                name="学生A",
                level=StudentLevel.AVERAGE,
                attitude=StudentAttitude.ACTIVE,
                learning_ability=6,
            ),
            rng=Mock(random=Mock(return_value=0.9)),  # 确定性：总是响应
        )

        checkpoint = Checkpoint(
            title="if 语句",
            key_point="条件判断的基础语法",
            checkpoint_question="什么是 if 语句？",
        )
        plan = CheckpointPlan(
            topic="Python 条件语句",
            teaching_mode="heuristic",
            checkpoints=[checkpoint],
        )

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager,
        )

        ws_messages = []

        async def ws_callback(msg):
            ws_messages.append(msg)
            data = msg["data"]
            cp = data["checkpoint"]
            print(f"\n[WebSocket 推送] type={msg['type']}, state={cp['state']}, title={cp['title']}")

        orchestrator.set_ws_push_callback(ws_callback)

        print(f"\n{'=' * 60}")
        print("开始讲授检查点: if 语句 (heuristic 模式)")
        print(f"{'=' * 60}")
        await orchestrator._teach_checkpoint(checkpoint)

        # 打印所有消息
        print("\n[完整对话记录]:")
        print(f"{'-' * 60}")
        for msg in session_memory.message_history:
            sender = msg.sender
            msg_type = msg.message_type.value
            print(f"  [{sender}] ({msg_type}): {msg.content[:200]}")
        print(f"{'-' * 60}")

        # 验证: heuristic 模式应有 3 个状态变更
        state_change_msgs = [
            msg for msg in ws_messages if msg["type"] == "checkpoint_state_change"
        ]
        assert len(state_change_msgs) == 3
        assert state_change_msgs[0]["data"]["checkpoint"]["state"] == "teaching"
        assert state_change_msgs[1]["data"]["checkpoint"]["state"] == "questions"
        assert state_change_msgs[2]["data"]["checkpoint"]["state"] == "complete"
        assert checkpoint.state == CheckpointState.COMPLETE

        print(f"\n验证通过: 收到 {len(state_change_msgs)} 个 WebSocket 推送事件 (teaching → questions → complete)")

    asyncio.run(_test())
