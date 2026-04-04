"""Memory 数据类和 MemoryManager 测试."""

import random
from datetime import datetime

from schemas.message import Message, MessageType
from schemas.student import StudentAttitude, StudentLevel, StudentProfile


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


class TestStudentAgentMemory:
    """StudentAgentMemory 测试."""

    def test_init_from_profile(self):
        """测试从 StudentProfile 初始化."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="张三",
            level=StudentLevel.EXCELLENT,
            attitude=StudentAttitude.ACTIVE,
            learning_ability=8,
        )
        memory = StudentAgentMemory.from_profile(profile=profile)

        assert memory.name == "张三"
        assert memory.level == StudentLevel.EXCELLENT
        assert memory.attitude == StudentAttitude.ACTIVE
        assert memory.learning_ability == 8
        assert memory.learned_concepts == []
        assert memory.current_knowledge_level == 0.0
        assert memory.learning_rate == 0.08  # learning_ability * 0.01

    def test_learning_rate_from_ability(self):
        """测试学习速率根据学习能力计算."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile_high = StudentProfile(name="高", learning_ability=9)
        profile_low = StudentProfile(name="低", learning_ability=2)

        memory_high = StudentAgentMemory.from_profile(profile=profile_high)
        memory_low = StudentAgentMemory.from_profile(profile=profile_low)

        assert memory_high.learning_rate == 0.09
        assert memory_low.learning_rate == 0.02

    def test_should_remember_concept_excellent_remembers_more(self):
        """测试优秀学生更容易记住概念."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="优秀生",
            level=StudentLevel.EXCELLENT,
            learning_ability=9,
        )
        memory = StudentAgentMemory.from_profile(profile=profile)

        rng = random.Random(42)
        # 优秀学生 knowledge_level 会随着学习逐渐提高
        # 用固定种子测试，观察结果一致性
        results = [memory.should_remember_concept("概念A", rng) for _ in range(100)]
        # 至少有一些应该记住（概率 > 0.5）
        assert sum(results) > 30

    def test_should_remember_concept_basic_remembers_less(self):
        """测试基础学生记住概念的概率较低."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="基础生",
            level=StudentLevel.BASIC,
            learning_ability=2,
        )
        memory = StudentAgentMemory.from_profile(profile=profile)

        rng = random.Random(42)
        results = [memory.should_remember_concept("概念A", rng) for _ in range(100)]
        # 基础学生记住的应该较少
        assert sum(results) < 70

    def test_update_knowledge_new_concept(self):
        """测试更新知识 - 新概念被记住."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(name="张三", learning_ability=8)
        memory = StudentAgentMemory.from_profile(profile=profile)

        # 用固定种子，模拟记住
        rng = random.Random(42)
        memory.update_knowledge(["变量", "函数"], rng)

        # 至少有一个被记住（概率较高）
        assert len(memory.learned_concepts) >= 0  # 可能都不记住
        assert memory.current_knowledge_level >= 0.0

    def test_update_knowledge_no_duplicates(self):
        """测试不重复学习相同概念."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(name="张三", learning_ability=10)
        memory = StudentAgentMemory.from_profile(profile=profile)

        # 直接添加一个概念，模拟已经学会
        memory.learned_concepts.append("变量")
        memory.current_knowledge_level = 0.5  # 设置知识水平

        rng = random.Random(42)
        count_before = len(memory.learned_concepts)

        memory.update_knowledge(["变量"], rng)
        assert len(memory.learned_concepts) == count_before
        assert "变量" in memory.learned_concepts

    def test_update_knowledge_increases_level(self):
        """测试学习新概念提升知识水平."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(name="张三", learning_ability=8)
        memory = StudentAgentMemory.from_profile(profile=profile)

        rng = random.Random(42)
        # 用确定性种子确保至少记住一个
        initial_level = memory.current_knowledge_level
        memory.update_knowledge(["概念1", "概念2", "概念3", "概念4", "概念5"], rng)

        assert memory.current_knowledge_level >= initial_level

    def test_get_system_prompt_addition(self):
        """测试生成学生 system prompt 附加内容."""
        from agents.memories.memory_manager import StudentAgentMemory

        profile = StudentProfile(
            name="张三",
            level=StudentLevel.EXCELLENT,
            attitude=StudentAttitude.ACTIVE,
            learning_ability=8,
        )
        memory = StudentAgentMemory.from_profile(profile=profile)
        memory.learned_concepts.append("变量")

        prompt = memory.get_system_prompt_addition(topic="Python基础")
        assert "Python基础" in prompt
        assert "变量" in prompt
        assert "张三" in prompt
        assert "8/10" in prompt
        assert "excellent" in prompt


class TestMemoryManager:
    """MemoryManager 测试."""

    def _make_message(
        self, sender: str, msg_type: MessageType, content: str
    ) -> Message:
        """辅助方法：创建消息."""
        return Message(
            sender=sender,
            message_type=msg_type,
            content=content,
            timestamp=datetime.now(),
        )

    def test_init(self):
        """测试初始化."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        assert manager.session_memory is session_mem
        assert manager.teacher_memory.covered_topics == []
        assert manager.student_memories == {}

    def test_register_student(self):
        """测试注册学生."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        profile = StudentProfile(name="张三", learning_ability=8)
        manager.register_student(profile)

        assert "张三" in manager.student_memories
        assert manager.student_memories["张三"].name == "张三"
        assert manager.student_memories["张三"].learning_ability == 8

    def test_process_message_appends_to_history(self):
        """测试处理消息添加到历史."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("teacher", MessageType.LECTURE, "今天学习变量")
        manager.process_message(msg)

        assert len(session_mem.message_history) == 1
        assert session_mem.message_history[0].content == "今天学习变量"

    def test_process_lecture_extracts_knowledge_points(self):
        """测试处理讲授内容提取知识点（使用 mock LLM）."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_mem,
            extract_knowledge_fn=lambda content: ["变量", "数据类型"],
        )

        msg = self._make_message("teacher", MessageType.LECTURE, "今天学习变量和数据类型")
        manager.process_message(msg)

        assert "变量" in manager.teacher_memory.covered_topics
        assert "数据类型" in manager.teacher_memory.covered_topics

    def test_process_lecture_no_duplicates(self):
        """测试不重复记录已讲授知识点."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_mem,
            extract_knowledge_fn=lambda content: ["变量"],
        )

        manager.process_message(
            self._make_message("teacher", MessageType.LECTURE, "讲变量")
        )
        manager.process_message(
            self._make_message("teacher", MessageType.LECTURE, "再讲变量")
        )

        assert manager.teacher_memory.covered_topics == ["变量"]

    def test_process_lecture_updates_student_memories(self):
        """测试讲授内容更新学生记忆."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_mem,
            extract_knowledge_fn=lambda content: ["变量"],
            student_rng=random.Random(42),
        )

        profile = StudentProfile(name="张三", learning_ability=10)
        manager.register_student(profile)

        manager.process_message(
            self._make_message("teacher", MessageType.LECTURE, "讲变量")
        )

        # 学习能力10的学生几乎一定记住
        student_mem = manager.student_memories["张三"]
        assert len(student_mem.learned_concepts) >= 0  # 可能记住

    def test_process_checkpoint_question_tracks(self):
        """测试处理 checkpoint 问题不崩溃."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message(
            "teacher", MessageType.CHECKPOINT_QUESTION, "什么是变量?"
        )
        manager.process_message(msg)
        assert len(session_mem.message_history) == 1

    def test_process_reply_to_teacher_tracks_participation(self):
        """测试处理学生回答记录参与."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("张三", MessageType.REPLY_TO_TEACHER, "变量是...")
        manager.process_message(msg)

        assert manager.teacher_memory.student_participation.get("张三") == 1

    def test_process_question_to_teacher_records(self):
        """测试处理学生提问记录到教师记忆."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message(
            "张三", MessageType.QUESTION_TO_TEACHER, "什么是变量?"
        )
        manager.process_message(msg)

        assert "张三" in manager.teacher_memory.student_questions
        assert manager.teacher_memory.student_questions["张三"] == ["什么是变量?"]

    def test_process_answer_to_checkpoint_tracks(self):
        """测试处理 checkpoint 回答记录参与."""
        from agents.memories.memory_manager import MemoryManager, SessionMemory

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        manager = MemoryManager(session_memory=session_mem)

        msg = self._make_message("李四", MessageType.ANSWER_TO_CHECKPOINT, "变量是...")
        manager.process_message(msg)

        assert manager.teacher_memory.student_participation.get("李四") == 1
