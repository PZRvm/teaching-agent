"""Pydantic schema validation tests.

Tests are written FIRST (TDD) - they will fail because schemas don't exist yet.
"""

import pytest
from pydantic import ValidationError


class TestStudentProfile:
    """Test StudentProfile schema validation."""

    def test_valid_student_profile(self):
        """Test creating valid student profile."""
        from schemas.student import StudentAttitude, StudentLevel, StudentProfile

        profile = StudentProfile(
            name="Alice",
            gender="女",
            level=StudentLevel.EXCELLENT,
            attitude=StudentAttitude.ACTIVE,
            learning_ability=8,
        )
        assert profile.name == "Alice"
        assert profile.level == StudentLevel.EXCELLENT
        assert profile.learning_ability == 8

    def test_name_too_short(self):
        """Test name validation - too short."""
        from schemas.student import StudentLevel, StudentProfile

        with pytest.raises(ValidationError) as exc_info:
            StudentProfile(
                name="",
                level=StudentLevel.AVERAGE,
                learning_ability=5,
            )
        assert (
            "min_length" in str(exc_info.value).lower() or "at least" in str(exc_info.value).lower()
        )

    def test_name_too_long(self):
        """Test name validation - too long."""
        from schemas.student import StudentLevel, StudentProfile

        with pytest.raises(ValidationError):
            StudentProfile(
                name="A" * 21,
                level=StudentLevel.AVERAGE,
                learning_ability=5,
            )

    def test_name_whitespace_only(self):
        """Test name validation - whitespace only."""
        from schemas.student import StudentLevel, StudentProfile

        with pytest.raises(ValidationError):
            StudentProfile(
                name="   ",
                level=StudentLevel.AVERAGE,
                learning_ability=5,
            )

    def test_learning_ability_out_of_range_low(self):
        """Test learning_ability validation - too low."""
        from schemas.student import StudentLevel, StudentProfile

        with pytest.raises(ValidationError):
            StudentProfile(
                name="Bob",
                level=StudentLevel.BASIC,
                learning_ability=0,
            )

    def test_learning_ability_out_of_range_high(self):
        """Test learning_ability validation - too high."""
        from schemas.student import StudentLevel, StudentProfile

        with pytest.raises(ValidationError):
            StudentProfile(
                name="Charlie",
                level=StudentLevel.EXCELLENT,
                learning_ability=11,
            )

    def test_default_values(self):
        """Test default values for optional fields."""
        from schemas.student import StudentAttitude, StudentLevel, StudentProfile

        profile = StudentProfile(
            name="David",
            learning_ability=5,
        )
        assert profile.level == StudentLevel.AVERAGE
        assert profile.attitude == StudentAttitude.NEUTRAL
        assert profile.gender is None
        assert profile.special_traits == []


class TestRandomClassConfig:
    """Test RandomClassConfig schema validation."""

    def test_valid_random_config(self):
        """Test creating valid random class config."""
        from schemas.student import RandomClassConfig

        config = RandomClassConfig(
            total_students=30,
            level_distribution={"excellent": 0.3, "average": 0.5, "basic": 0.2},
            attitude_distribution={"active": 0.3, "neutral": 0.5, "passive": 0.2},
            random_seed=42,
        )
        assert config.total_students == 30
        assert config.random_seed == 42

    def test_level_distribution_not_sum_to_one(self):
        """Test level distribution validation - doesn't sum to 1."""
        from schemas.student import RandomClassConfig

        with pytest.raises(ValidationError) as exc_info:
            RandomClassConfig(
                total_students=20,
                level_distribution={"excellent": 0.5, "average": 0.6, "basic": 0.2},
            )
        assert (
            "分布比例总和必须为1.0" in str(exc_info.value) or "sum" in str(exc_info.value).lower()
        )

    def test_total_students_too_small(self):
        """Test total_students validation - too small."""
        from schemas.student import RandomClassConfig

        with pytest.raises(ValidationError):
            RandomClassConfig(
                total_students=1,
            )

    def test_total_students_too_large(self):
        """Test total_students validation - too large."""
        from schemas.student import RandomClassConfig

        with pytest.raises(ValidationError):
            RandomClassConfig(
                total_students=51,
            )


class TestTeachingSessionCreate:
    """Test TeachingSessionCreate schema validation."""

    def test_valid_session_create(self):
        """Test creating valid teaching session."""
        from schemas.student import StudentCreateRequest, StudentProfile
        from schemas.teaching_session import TeachingMode, TeachingSessionCreate

        session = TeachingSessionCreate(
            teaching_mode=TeachingMode.DIDACTIC,
            topic="Python Basics",
            students_config=StudentCreateRequest(
                source="manual",
                manual_students=[
                    StudentProfile(name="Alice", learning_ability=7),
                    StudentProfile(name="Bob", learning_ability=5),
                ],
            ),
            duration_seconds=1800,
        )
        assert session.teaching_mode == TeachingMode.DIDACTIC
        assert session.topic == "Python Basics"
        assert session.duration_seconds == 1800

    def test_topic_too_long(self):
        """Test topic validation - too long."""
        from schemas.student import StudentCreateRequest
        from schemas.teaching_session import TeachingMode, TeachingSessionCreate

        with pytest.raises(ValidationError):
            TeachingSessionCreate(
                teaching_mode=TeachingMode.HEURISTIC,
                topic="A" * 201,
                students_config=StudentCreateRequest(source="random"),
            )

    def test_duration_too_short(self):
        """Test duration_seconds validation - too short."""
        from schemas.student import StudentCreateRequest
        from schemas.teaching_session import TeachingMode, TeachingSessionCreate

        with pytest.raises(ValidationError):
            TeachingSessionCreate(
                teaching_mode=TeachingMode.DISCUSSION,
                topic="Valid Topic",
                students_config=StudentCreateRequest(source="random"),
                duration_seconds=30,
            )

    def test_optional_duration(self):
        """Test duration_seconds is optional."""
        from schemas.student import StudentCreateRequest
        from schemas.teaching_session import TeachingMode, TeachingSessionCreate

        session = TeachingSessionCreate(
            teaching_mode=TeachingMode.DIDACTIC,
            topic="Test Topic",
            students_config=StudentCreateRequest(source="random"),
        )
        assert session.duration_seconds is None


class TestMessage:
    """Test Message schema validation."""

    def test_valid_message(self):
        """Test creating valid message."""
        from schemas.message import Message, MessageType

        message = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="Welcome to the class!",
        )
        assert message.sender == "teacher"
        assert message.message_type == MessageType.LECTURE

    def test_content_empty(self):
        """Test content validation - empty."""
        from schemas.message import Message, MessageType

        with pytest.raises(ValidationError):
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="",
            )

    def test_message_create_with_session_id(self):
        """Test MessageCreate schema."""
        from schemas.message import MessageCreate, MessageType

        message_create = MessageCreate(
            session_id=1,
            sender="Alice",
            message_type=MessageType.QUESTION_TO_TEACHER,
            content="I have a question",
        )
        assert message_create.session_id == 1
        assert message_create.sender == "Alice"

    def test_message_with_receiver(self):
        """Test Message 支持 receiver 字段."""
        from datetime import datetime

        from schemas.message import Message, MessageType

        msg = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="Hello everyone",
            receiver="all",
            timestamp=datetime.now(),
        )
        assert msg.receiver == "all"
