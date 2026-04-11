"""观察模式 Pydantic schemas."""

from pydantic import BaseModel, Field

from schemas.student import StudentProfile


class ObservationConfig(BaseModel):
    """观察模式配置."""

    topic: str = Field(min_length=1, description="教学主题")
    teaching_mode: str = Field(description="教学模式 (didactic/heuristic/discussion)")
    students: list[StudentProfile] = Field(min_length=1, description="学生列表")


class ObservationStartResponse(BaseModel):
    """观察模式启动响应."""

    session_id: int = Field(description="会话ID")
    status: str = Field(description="会话状态")


class ObservationMetrics(BaseModel):
    """观察模式指标."""

    total_checkpoints: int = Field(description="总检查点数")
    completed_checkpoints: int = Field(description="已完成检查点数")
    total_messages: int = Field(description="总消息数")
    student_participation: dict[str, int] = Field(default_factory=dict, description="学生参与次数")


class ObservationReport(BaseModel):
    """观察模式报告."""

    session_id: int = Field(description="会话ID")
    topic: str = Field(description="教学主题")
    teaching_mode: str = Field(description="教学模式")
    metrics: ObservationMetrics = Field(description="教学指标")
    messages: list[str] = Field(description="消息摘要")
