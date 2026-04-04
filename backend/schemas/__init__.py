"""Pydantic schemas 包."""

# ============== Student Related ==============
# ============== Message Related ==============
from schemas.message import (
    Message,
    MessageCreate,
    MessageResponse,
    MessageType,
)
from schemas.student import (
    RandomClassConfig,
    StudentAttitude,
    StudentCreateRequest,
    StudentLevel,
    StudentProfile,
)

# ============== Teaching Session Related ==============
from schemas.teaching_session import (
    SessionPhase,
    TeachingMode,
    TeachingSessionCreate,
    TeachingSessionResponse,
)

__all__ = [
    # Student
    "StudentProfile",
    "StudentLevel",
    "StudentAttitude",
    "RandomClassConfig",
    "StudentCreateRequest",
    # Message
    "MessageType",
    "Message",
    "MessageCreate",
    "MessageResponse",
    # Teaching Session
    "TeachingMode",
    "SessionPhase",
    "TeachingSessionCreate",
    "TeachingSessionResponse",
]
