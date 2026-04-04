"""Pydantic schemas for teaching session related models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============== Enums ==============


class TeachingMode(str, Enum):
    """教学模式枚举"""

    DIDACTIC = "didactic"
    HEURISTIC = "heuristic"
    DISCUSSION = "discussion"


class SessionPhase(str, Enum):
    """会话阶段枚举"""

    PARAMETER_SETTING = "parameter_setting"
    TEACHING = "teaching"
    ENDED = "ended"


class StudentLevel(str, Enum):
    """学生水平枚举"""

    EXCELLENT = "excellent"
    AVERAGE = "average"
    BASIC = "basic"


class StudentAttitude(str, Enum):
    """学生态度枚举"""

    ACTIVE = "active"
    NEUTRAL = "neutral"
    PASSIVE = "passive"


class MessageType(str, Enum):
    """消息类型枚举"""

    LECTURE = "lecture"
    CHECKPOINT_QUESTION = "checkpoint_question"
    REPLY_TO_TEACHER = "reply_to_teacher"
    ASSIGN_HOMEWORK = "assign_homework"
    END_FEEDBACK = "end_feedback"
    HOMEWORK_FEEDBACK = "homework_feedback"
    QUESTION_TO_TEACHER = "question_to_teacher"
    ANSWER_TO_CHECKPOINT = "answer_to_checkpoint"
    HOMEWORK_SUBMISSION = "homework_submission"
    FEEDBACK_SUBMISSION = "feedback_submission"


# ============== Student Related Schemas ==============


class StudentProfile(BaseModel):
    """学生配置文件"""

    name: str = Field(min_length=1, max_length=20)
    gender: str | None = Field(None, max_length=10)
    level: StudentLevel = Field(default=StudentLevel.AVERAGE)
    attitude: StudentAttitude = Field(default=StudentAttitude.NEUTRAL)
    learning_ability: int = Field(ge=1, le=10)
    background: str | None = Field(None)
    special_traits: list[str] | None = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("名字不能为空")
        return v.strip()


class RandomClassConfig(BaseModel):
    """随机班级生成配置"""

    total_students: int = Field(ge=2, le=50)
    level_distribution: dict = Field(default={"excellent": 0.3, "average": 0.5, "basic": 0.2})
    attitude_distribution: dict = Field(default={"active": 0.3, "neutral": 0.5, "passive": 0.2})
    random_seed: int | None = Field(None)

    @field_validator("level_distribution", "attitude_distribution")
    @classmethod
    def distribution_sum_to_one(cls, v: dict) -> dict:
        if not (0.99 <= sum(v.values()) <= 1.01):
            raise ValueError("分布比例总和必须为1.0")
        return v


class StudentCreateRequest(BaseModel):
    """统一的学生创建请求"""

    source: str = Field(description="创建方式: manual/random/json")
    manual_students: list[StudentProfile] | None = Field(None)
    random_config: RandomClassConfig | None = Field(None)
    json_data: str | None = Field(None)


# ============== Session Related Schemas ==============


class TeachingSessionCreate(BaseModel):
    """创建教学会话请求"""

    teaching_mode: TeachingMode
    topic: str = Field(min_length=1, max_length=200)
    students_config: StudentCreateRequest
    duration_seconds: int | None = Field(None, ge=60)


class TeachingSessionResponse(BaseModel):
    """教学会话响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    teaching_mode: TeachingMode
    topic: str
    students_config: dict
    duration_seconds: int | None
    status: str
    start_time: datetime
    end_time: datetime | None


# ============== Message Related Schemas ==============


class Message(BaseModel):
    """消息数据模型"""

    sender: str = Field(description="发送者")
    message_type: MessageType = Field(description="消息类型")
    content: str = Field(min_length=1, description="消息内容")
    timestamp: datetime | None = Field(None)


class MessageCreate(BaseModel):
    """创建消息请求"""

    session_id: int = Field(description="会话ID")
    sender: str = Field(description="发送者")
    message_type: MessageType = Field(description="消息类型")
    content: str = Field(min_length=1, description="消息内容")


class MessageResponse(BaseModel):
    """消息响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sender: str
    message_type: MessageType
    content: str
    timestamp: datetime
