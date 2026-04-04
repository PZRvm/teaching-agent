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


class TestTeacherAgentMemory:
    """TeacherAgentMemory 测试."""

    def test_init_default_values(self):
        """测试默认初始化."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        assert memory.covered_topics == []
        assert memory.student_questions == {}
        assert memory.student_participation == {}
        assert memory.teaching_progress == 0.0
        assert memory.student_misconceptions == {}

    def test_record_covered_topic(self):
        """测试记录已讲授主题."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_covered_topic("变量与数据类型")
        assert "变量与数据类型" in memory.covered_topics

    def test_record_covered_topic_no_duplicates(self):
        """测试不重复记录相同主题."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_covered_topic("变量与数据类型")
        memory.record_covered_topic("变量与数据类型")
        assert memory.covered_topics == ["变量与数据类型"]

    def test_record_student_question(self):
        """测试记录学生提问."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_student_question("张三", "什么是变量?")
        assert memory.student_questions == {"张三": ["什么是变量?"]}

    def test_record_student_question_accumulates(self):
        """测试学生提问累积."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_student_question("张三", "什么是变量?")
        memory.record_student_question("张三", "那函数呢?")
        assert len(memory.student_questions["张三"]) == 2

    def test_record_student_participation(self):
        """测试记录学生参与."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_student_participation("张三")
        memory.record_student_participation("张三")
        memory.record_student_participation("李四")
        assert memory.student_participation == {"张三": 2, "李四": 1}

    def test_record_misconception(self):
        """测试记录学生误解."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_misconception("张三", "认为变量不需要声明")
        assert memory.student_misconceptions == {"张三": ["认为变量不需要声明"]}

    def test_get_system_prompt_addition(self):
        """测试生成教师 system prompt 附加内容."""
        from agents.memories.memory_manager import TeacherAgentMemory

        memory = TeacherAgentMemory()
        memory.record_covered_topic("变量与数据类型")
        memory.record_covered_topic("条件语句")
        memory.record_student_participation("张三")

        prompt = memory.get_system_prompt_addition(topic="Python基础")
        assert "Python基础" in prompt
        assert "变量与数据类型" in prompt
        assert "条件语句" in prompt
        assert "张三" in prompt
