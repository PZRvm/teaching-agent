"""Session 相关的 Pydantic schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MessageType(str, Enum):
    """消息类型枚举"""

    LECTURE = "lecture"
    CHECKPOINT_QUESTION = "checkpoint_question"
    REPLY_TO_TEACHER = "reply_to_teacher"
    REPLY_TO_STUDENT = "reply_to_student"
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


# WebSocket 事件 schemas


class WsEventBase(BaseModel):
    """WebSocket 事件基类."""

    type: str
    session_id: int


class WsConnectedEvent(WsEventBase):
    """WebSocket 连接确认事件."""

    type: str = "connected"
    mode: str = Field(description="会话模式 (observation/teacher)")


class WsMessageEvent(WsEventBase):
    """WebSocket 消息事件（教师讲授/学生回答等）."""

    type: str = "message"
    sender: str
    message_type: str
    content: str
    receiver: str = "all"


class WsCheckpointStateEvent(WsEventBase):
    """WebSocket 检查点状态变更事件."""

    type: str = "checkpoint_state_change"
    index: int
    checkpoint: dict
    progress: dict


class WsStudentAnswerEvent(WsEventBase):
    """WebSocket 学生回答事件（教师模式实时推送）."""

    type: str = "student_answer"
    student_name: str
    content: str
    message_type: str


class WsSessionStateEvent(WsEventBase):
    """WebSocket 会话状态事件."""

    type: str = "session_state"
    teaching_mode: str
    phase: str
    checkpoint_index: int = 0
    total_checkpoints: int = 0


class WsSessionEndEvent(WsEventBase):
    """WebSocket 会话结束事件."""

    type: str = "session_end"
    reason: str
