"""SessionOrchestrator - 观察模式核心控制器."""

import random
from collections.abc import Callable

from agents.student_agent import StudentAgent
from models.checkpoint.schemas import Checkpoint, CheckpointState


class SessionOrchestrator:
    """观察模式自动教学流程编排器.

    基于检查点系统驱动教学流程：
    - 遍历检查点数组
    - 协调教师和学生 agent 交互
    - 通过 WebSocket 推送状态更新
    - 集成 MemoryManager 记录教学过程
    """

    def __init__(
        self,
        *,
        teacher_agent,
        student_agents: list,
        checkpoint_plan,
        memory_manager,
    ):
        """初始化编排器.

        Args:
            teacher_agent: 教师 agent
            student_agents: 学生 agent 列表
            checkpoint_plan: 检查点计划
            memory_manager: 记忆管理器
        """
        self.teacher_agent = teacher_agent
        self.student_agents = student_agents
        self.checkpoint_plan = checkpoint_plan
        self.memory_manager = memory_manager

        # WebSocket 推送回调（可选，用于测试）
        self._ws_push_callback: Callable | None = None

    def set_ws_push_callback(self, callback: Callable) -> None:
        """设置 WebSocket 推送回调（用于测试）."""
        self._ws_push_callback = callback

    async def run_autonomous_session(self) -> None:
        """运行自动教学会话（基于检查点）.

        遍历所有检查点，对每个检查点执行教学流程：
        - 灌输式: TEACHING → COMPLETE
        - 启发式/讨论式: TEACHING → QUESTIONS → COMPLETE

        最后一个检查点完成后布置作业和收集反馈。
        """
        for i, checkpoint in enumerate(self.checkpoint_plan.checkpoints):
            # 更新当前索引
            self.checkpoint_plan.current_index = i

            # 教授当前检查点
            await self._teach_checkpoint(checkpoint)

        # 所有检查点完成后，布置作业和收集反馈
        await self._assign_homework()
        await self._collect_homework_and_feedback()

    async def _teach_checkpoint(self, checkpoint: Checkpoint) -> None:
        """教授单个检查点.

        Args:
            checkpoint: 当前检查点
        """
        # TEACHING 状态
        checkpoint.state = CheckpointState.TEACHING
        await self._ws_push_checkpoint_state(checkpoint)

        # 传授知识点
        await self._deliver_checkpoint_lecture(checkpoint)

        # 根据教学模式决定是否进入 QUESTIONS 状态
        mode = self.checkpoint_plan.teaching_mode

        if mode in ("heuristic", "discussion"):
            # QUESTIONS 状态
            checkpoint.state = CheckpointState.QUESTIONS
            await self._ws_push_checkpoint_state(checkpoint)

            # 处理学生互动
            await self._handle_checkpoint_questions(checkpoint)

        # COMPLETE 状态
        checkpoint.state = CheckpointState.COMPLETE
        await self._ws_push_checkpoint_state(checkpoint)

        # 记录知识点到 MemoryManager
        await self._trigger_observer_learning_for_checkpoint(checkpoint)

    async def _deliver_checkpoint_lecture(self, checkpoint: Checkpoint) -> None:
        """传授检查点知识点.

        Args:
            checkpoint: 当前检查点

        通过 TeacherAgentMemory 将 checkpoint.key_point 注入到教师 agent 的 system prompt，
        使教师专门讲授该知识点。
        """
        # 记录当前知识点到教师记忆
        self.memory_manager.teacher_memory.record_covered_topic(checkpoint.key_point)

        # 调用教师 agent 生成讲授内容（同步方法）
        lecture_content = self.teacher_agent.deliver_lecture()

        # 记录到会话记忆
        from datetime import datetime

        from schemas.message import Message, MessageType

        message = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content=lecture_content,
            receiver="all",
            timestamp=datetime.now(),
        )

        self.memory_manager.process_message(message)

    async def _handle_checkpoint_questions(self, checkpoint: Checkpoint) -> None:
        """处理检查点问题环节.

        Args:
            checkpoint: 当前检查点

        启发式和讨论式模式下，教师提出 checkpoint_question，
        收集学生回答，并提供反馈。
        """
        # 教师提出检查点问题（同步方法）
        question_content = self.teacher_agent.ask_checkpoint_question()

        # 记录问题到会话记忆
        from datetime import datetime

        from schemas.message import Message, MessageType

        message = Message(
            sender="teacher",
            message_type=MessageType.CHECKPOINT_QUESTION,
            content=question_content,
            receiver="all",
            timestamp=datetime.now(),
        )

        self.memory_manager.process_message(message)

        # 收集学生回答
        await self._collect_student_answers()

    async def _collect_student_answers(self) -> None:
        """收集学生回答（场景 A: 教师提问）.

        教师提问后，学生基于 should_respond() 决定是否回答。
        如果无人回答，教师指定某个学生回答。
        """

        responding_students = []

        # 让每个学生决定是否响应
        for student in self.student_agents:
            if student.should_respond():
                responding_students.append(student)

        # 如果无人响应，随机指定一个学生
        if not responding_students:
            designated_student = random.choice(self.student_agents)
            await self._single_student_answer(designated_student)
        else:
            # 收集所有响应学生的回答
            for student in responding_students:
                answer = student.answer_question("Please answer the question.")
                self._record_student_message(student.profile.name, answer)

    async def _single_student_answer(self, student: "StudentAgent") -> None:
        """让被指定的学生回答.

        Args:
            student: 被指定的学生 agent
        """
        answer = student.answer_question("Please answer the question.")
        self._record_student_message(student.profile.name, answer)

    def _record_student_message(self, student_name: str, content: str) -> None:
        """记录学生消息到记忆.

        Args:
            student_name: 学生名称
            content: 消息内容
        """
        from datetime import datetime

        from schemas.message import Message, MessageType

        message = Message(
            sender=student_name,
            message_type=MessageType.ANSWER_TO_CHECKPOINT,
            content=content,
            receiver="teacher",
            timestamp=datetime.now(),
        )

        self.memory_manager.process_message(message)

    async def _assign_homework(self) -> None:
        """布置作业."""
        # 调用教师 agent 布置作业（同步方法）
        homework_content = self.teacher_agent.assign_homework()

        # 记录到会话记忆
        from datetime import datetime

        from schemas.message import Message, MessageType

        message = Message(
            sender="teacher",
            message_type=MessageType.ASSIGN_HOMEWORK,
            content=homework_content,
            receiver="all",
            timestamp=datetime.now(),
        )

        self.memory_manager.process_message(message)

    async def _collect_homework_and_feedback(self) -> None:
        """收集作业和反馈."""
        from datetime import datetime

        from schemas.message import Message, MessageType

        # 收集每个学生的作业
        for student in self.student_agents:
            # 学生提交作业（需要提供作业提示）
            homework = student.submit_homework("Please complete your homework.")
            homework_message = Message(
                sender=student.profile.name,
                message_type=MessageType.HOMEWORK_SUBMISSION,
                content=homework,
                receiver="teacher",
                timestamp=datetime.now(),
            )
            self.memory_manager.process_message(homework_message)

            # 教师批改作业并反馈（同步方法，需要学生名）
            feedback = self.teacher_agent.grade_homework(student.profile.name, homework)
            feedback_message = Message(
                sender="teacher",
                message_type=MessageType.HOMEWORK_FEEDBACK,
                content=feedback,
                receiver=student.profile.name,
                timestamp=datetime.now(),
            )
            self.memory_manager.process_message(feedback_message)

        # 教师总结反馈（同步方法）
        end_feedback = self.teacher_agent.end_feedback()
        end_message = Message(
            sender="teacher",
            message_type=MessageType.END_FEEDBACK,
            content=end_feedback,
            receiver="all",
            timestamp=datetime.now(),
        )
        self.memory_manager.process_message(end_message)

    async def _trigger_observer_learning_for_checkpoint(self, checkpoint: Checkpoint) -> None:
        """触发观察者学习检查点知识点.

        Args:
            checkpoint: 当前检查点

        将 checkpoint.key_point 作为"知识点"传递给 MemoryManager，
        让所有学生尝试学习（基于学习参数决定是否记住）。
        """
        # 将知识点记录到教师记忆中
        self.memory_manager.teacher_memory.record_covered_topic(checkpoint.key_point)

        # 尝试让每个学生学习该知识点
        for student in self.student_agents:
            # 学生尝试记住知识点（使用学生的 rng）
            if student.memory.should_remember_concept(checkpoint.key_point, student.rng):
                student.memory.update_knowledge([checkpoint.key_point], student.rng)

    async def _ws_push_checkpoint_state(self, checkpoint: Checkpoint) -> None:
        """通过 WebSocket 推送检查点状态变更.

        Args:
            checkpoint: 当前检查点
        """
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
            # Check if callback is async or sync
            import inspect

            if inspect.iscoroutinefunction(self._ws_push_callback):
                await self._ws_push_callback(message)
            else:
                self._ws_push_callback(message)
