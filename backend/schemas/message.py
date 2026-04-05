"""消息相关的 Pydantic schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MessageType(str, Enum):
    """消息类型枚举"""

    LECTURE = "lecture"
    CHECKPOINT_QUESTION = "checkpoint_question"
    REPLY_TO_TEACHER = "reply_to_teacher"
    ASSIGN_HOMEWORK = "assign_homework"
    END_FEEDBACK = "end_feedback"
    HOMEWORK_FEEDBACK = "homework_feedback"
    QUESTION_TO_TEACHER = "question_to_teacher"
    TEACHER_REPLY = "teacher_reply"
    ANSWER_TO_CHECKPOINT = "answer_to_checkpoint"
    HOMEWORK_SUBMISSION = "homework_submission"
    FEEDBACK_SUBMISSION = "feedback_submission"


class Message(BaseModel):
    """消息数据模型"""

    sender: str = Field(description="发送者")
    message_type: MessageType = Field(description="消息类型")
    content: str = Field(min_length=1, description="消息内容")
    receiver: str = Field(default="all", description="接收者 (all/学生名称)")
    timestamp: datetime | None = Field(None)


class MessageCreate(BaseModel):
    """创建消息请求"""

    session_id: int = Field(description="会话ID")
    sender: str = Field(description="发送者")
    message_type: MessageType = Field(description="消息类型")
    content: str = Field(min_length=1, description="消息内容")
    receiver: str = Field(default="all", description="接收者")


class MessageResponse(BaseModel):
    """消息响应"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sender: str
    message_type: MessageType
    content: str
    receiver: str
    timestamp: datetime
