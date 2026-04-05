"""Checkpoint Pydantic schemas."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CheckpointState(str, Enum):
    """检查点状态枚举。"""
    PENDING = "pending"
    TEACHING = "teaching"
    QUESTIONS = "questions"
    COMPLETE = "complete"


class Checkpoint(BaseModel):
    """单个检查点的教学单元。"""

    title: str = Field(min_length=1, description="检查点标题")
    key_point: str = Field(min_length=1, description="本检查点的核心知识点")
    checkpoint_question: str = Field(min_length=1, description="检查理解的问题")
    state: CheckpointState = Field(default=CheckpointState.PENDING, description="检查点当前状态")


class CheckpointPlan(BaseModel):
    """一节课的完整检查点计划。"""

    topic: str = Field(description="教学主题")
    teaching_mode: str = Field(description="教学模式")
    checkpoints: list[Checkpoint] = Field(min_length=1, description="检查点列表")
    current_index: int = Field(default=0, ge=0, description="当前检查点索引")

    @field_validator("teaching_mode")
    @classmethod
    def validate_teaching_mode(cls, v: str) -> str:
        """验证教学模式是否为有效值。"""
        valid_modes = {"didactic", "heuristic", "discussion", "teacher"}
        if v not in valid_modes:
            raise ValueError(f"teaching_mode must be one of {valid_modes}, got '{v}'")
        return v
