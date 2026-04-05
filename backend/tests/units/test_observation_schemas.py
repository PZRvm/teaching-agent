"""观察模式 Schema 单元测试."""


class TestObservationSchemas:
    """Test observation mode schemas."""

    def test_observation_config_schema(self):
        """测试 ObservationConfig schema."""
        from models.observation.schemas import ObservationConfig
        from schemas.student import StudentAttitude, StudentLevel, StudentProfile

        config = ObservationConfig(
            topic="Python Basics",
            teaching_mode="heuristic",
            checkpoint_count=3,
            students=[
                StudentProfile(
                    name="Student1",
                    level=StudentLevel.AVERAGE,
                    attitude=StudentAttitude.NEUTRAL,
                    learning_ability=5,
                )
            ],
        )

        assert config.topic == "Python Basics"
        assert config.teaching_mode == "heuristic"
        assert len(config.students) == 1

    def test_observation_start_response_schema(self):
        """测试 ObservationStartResponse schema."""
        from models.observation.schemas import ObservationStartResponse

        response = ObservationStartResponse(session_id=1, status="running")

        assert response.session_id == 1
        assert response.status == "running"
