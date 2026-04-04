"""学生相关的 Pydantic schemas."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


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
