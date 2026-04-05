"""SessionOrchestrator - 观察模式核心控制器."""


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
