"""TeacherAgent 真实 LLM 集成测试.

使用真实 LLM API 测试 TeacherAgent 的讲授功能（流式输出）。
运行方式: pytest tests/integration/test_teacher_agent_real.py -v -s
"""

from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import itertools  # noqa: E402

import pytest  # noqa: E402

from agents.memories import SessionMemory  # noqa: E402
from agents.teacher_agent import TeacherAgent  # noqa: E402
from core.llm_client import LLMClient  # noqa: E402

_session_counter = itertools.count(10000)


@pytest.fixture(scope="module")
def real_llm():
    """创建真实 LLM 客户端."""
    return LLMClient.from_config()


class TestTeacherAgentRealLecture:
    """使用真实 LLM 流式输出测试 TeacherAgent 讲授功能."""

    @pytest.mark.integration
    def test_deliver_lecture_didactic(self, real_llm):
        """测试灌输式模式讲授（真实 LLM，流式输出）."""
        session_id = next(_session_counter)
        session_mem = SessionMemory(session_id=session_id, topic="Python变量与数据类型")

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=real_llm,
            teaching_mode="didactic",
        )

        print(f"\n{'=' * 60}")
        print("[灌输式] Python变量与数据类型")
        print(f"{'=' * 60}")

        chunks = []
        for chunk in agent.deliver_lecture_stream():
            print(chunk, end="", flush=True)
            chunks.append(chunk)

        print(f"\n{'=' * 60}\n")

        content = "".join(chunks)
        assert isinstance(content, str)
        assert len(content) > 50
        assert len(agent.session_memory.message_history) == 1

    @pytest.mark.integration
    def test_deliver_lecture_heuristic(self, real_llm):
        """测试启发式模式讲授（真实 LLM，流式输出）."""
        session_id = next(_session_counter)
        session_mem = SessionMemory(session_id=session_id, topic="Python条件语句")

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=real_llm,
            teaching_mode="heuristic",
        )

        print(f"\n{'=' * 60}")
        print("[启发式] Python条件语句")
        print(f"{'=' * 60}")

        chunks = []
        for chunk in agent.deliver_lecture_stream():
            print(chunk, end="", flush=True)
            chunks.append(chunk)

        print(f"\n{'=' * 60}\n")

        content = "".join(chunks)
        assert isinstance(content, str)
        assert len(content) > 50
        assert len(agent.session_memory.message_history) == 1

    @pytest.mark.integration
    def test_deliver_lecture_discussion(self, real_llm):
        """测试讨论式模式讲授（真实 LLM，流式输出）."""
        session_id = next(_session_counter)
        session_mem = SessionMemory(session_id=session_id, topic="Python循环结构")

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=real_llm,
            teaching_mode="discussion",
        )

        print(f"\n{'=' * 60}")
        print("[讨论式] Python循环结构")
        print(f"{'=' * 60}")

        chunks = []
        for chunk in agent.deliver_lecture_stream():
            print(chunk, end="", flush=True)
            chunks.append(chunk)

        print(f"\n{'=' * 60}\n")

        content = "".join(chunks)
        assert isinstance(content, str)
        assert len(content) > 50
        assert len(agent.session_memory.message_history) == 1
