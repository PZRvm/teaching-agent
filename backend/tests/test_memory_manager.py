"""Memory 数据类和 MemoryManager 测试."""

from datetime import datetime

from schemas.message import Message, MessageType


class TestSessionMemory:
    """SessionMemory 测试."""

    def test_init_default_values(self):
        """测试默认初始化."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")

        assert memory.session_id == 1
        assert memory.topic == "Python基础"
        assert memory.message_history == []
        assert memory.teaching_summary == ""
        assert memory.max_history_messages == 50
        assert memory.summary_update_interval == 10
        assert memory.last_summary_update == 0

    def test_should_update_summary_false_initially(self):
        """测试初始状态下不需要更新摘要."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        assert memory.should_update_summary() is False

    def test_should_update_summary_true_after_interval(self):
        """测试达到间隔后需要更新摘要."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        for i in range(10):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"知识点{i}",
                    timestamp=datetime.now(),
                )
            )
        assert memory.should_update_summary() is True

    def test_should_update_summary_false_below_interval(self):
        """测试未达到间隔不需要更新."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        for i in range(9):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"知识点{i}",
                    timestamp=datetime.now(),
                )
            )
        assert memory.should_update_summary() is False

    def test_should_update_summary_resets_after_mark(self):
        """测试标记更新后重置计数."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        for i in range(10):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"知识点{i}",
                    timestamp=datetime.now(),
                )
            )
        assert memory.should_update_summary() is True

        memory.mark_summary_updated()
        assert memory.should_update_summary() is False

    def test_get_recent_messages_returns_last_n(self):
        """测试获取最近 N 条消息."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础", max_history_messages=3)
        for i in range(5):
            memory.message_history.append(
                Message(
                    sender="teacher",
                    message_type=MessageType.LECTURE,
                    content=f"内容{i}",
                    timestamp=datetime.now(),
                )
            )
        recent = memory.get_recent_messages()
        assert len(recent) == 3
        assert recent[0].content == "内容2"
        assert recent[2].content == "内容4"

    def test_get_recent_messages_empty(self):
        """测试空历史返回空列表."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        assert memory.get_recent_messages() == []

    def test_get_agent_context(self):
        """测试获取 agent 上下文."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(
            session_id=1,
            topic="Python基础",
            teaching_summary="已讲授变量和数据类型",
        )
        memory.message_history.append(
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="今天学习变量",
                timestamp=datetime.now(),
            )
        )

        context = memory.get_agent_context()
        assert "Python基础" in context
        assert "已讲授变量和数据类型" in context
        assert "今天学习变量" in context

    def test_add_message(self):
        """测试添加消息."""
        from agents.memories.memory_manager import SessionMemory

        memory = SessionMemory(session_id=1, topic="Python基础")
        msg = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="测试内容",
            timestamp=datetime.now(),
        )
        memory.add_message(msg)
        assert len(memory.message_history) == 1
        assert memory.message_history[0].content == "测试内容"
