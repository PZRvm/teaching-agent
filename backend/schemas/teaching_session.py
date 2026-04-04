"""教学会话相关的 Pydantic schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from schemas.student import StudentCreateRequest


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
