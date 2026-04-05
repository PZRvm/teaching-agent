"""Checkpoint schema 单元测试."""

import pytest
from pydantic import ValidationError

from models.checkpoint.schemas import (
    Checkpoint,
    CheckpointPlan,
    CheckpointState,
)


class TestCheckpointState:
    """CheckpointState 枚举测试."""

    def test_four_states_exist(self):
        assert CheckpointState.PENDING == "pending"
        assert CheckpointState.TEACHING == "teaching"
        assert CheckpointState.QUESTIONS == "questions"
        assert CheckpointState.COMPLETE == "complete"

    def test_state_values_are_strings(self):
        for state in CheckpointState:
            assert isinstance(state.value, str)


class TestCheckpoint:
    """Checkpoint 模型测试."""

    def test_valid_checkpoint(self):
        cp = Checkpoint(
            title="Python 变量与数据类型",
            key_point="变量和数据类型的基本概念",
            checkpoint_question="Python 中有哪些基本数据类型?",
        )
        assert cp.title == "Python 变量与数据类型"
        assert cp.state == CheckpointState.PENDING

    def test_default_state_is_pending(self):
        cp = Checkpoint(
            title="test",
            key_point="知识点",
            checkpoint_question="q?",
        )
        assert cp.state == CheckpointState.PENDING

    def test_title_min_length(self):
        with pytest.raises(ValidationError):
            Checkpoint(
                title="",
                key_point="p1",
                checkpoint_question="q?",
            )

    def test_key_point_min_length(self):
        with pytest.raises(ValidationError):
            Checkpoint(
                title="test",
                key_point="",
                checkpoint_question="q?",
            )

    def test_checkpoint_question_min_length(self):
        with pytest.raises(ValidationError):
            Checkpoint(
                title="test",
                key_point="p1",
                checkpoint_question="",
            )

    def test_state_can_be_set_to_teaching(self):
        cp = Checkpoint(
            title="test",
            key_point="p1",
            checkpoint_question="q?",
            state=CheckpointState.TEACHING,
        )
        assert cp.state == CheckpointState.TEACHING

    def test_json_round_trip(self):
        """Checkpoint 可正确序列化和反序列化。"""
        cp = Checkpoint(
            title="Python 变量与数据类型",
            key_point="变量的命名规则, int/float/str/bool 类型",
            checkpoint_question="Python 中有哪些基本数据类型?",
            state=CheckpointState.QUESTIONS,
        )
        json_str = cp.model_dump_json()
        restored = Checkpoint.model_validate_json(json_str)
        assert restored.title == cp.title
        assert restored.state == CheckpointState.QUESTIONS
        assert restored.key_point == cp.key_point


class TestCheckpointPlan:
    """CheckpointPlan 模型测试."""

    def _make_plan(self, **kwargs) -> CheckpointPlan:
        defaults = {
            "topic": "Python 基础入门",
            "teaching_mode": "heuristic",
            "checkpoints": [
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str, bool",
                    checkpoint_question="q?",
                )
            ],
        }
        defaults.update(kwargs)
        return CheckpointPlan(**defaults)

    def test_valid_plan(self):
        plan = self._make_plan()
        assert plan.topic == "Python 基础入门"
        assert plan.current_index == 0

    def test_default_current_index_is_zero(self):
        plan = self._make_plan()
        assert plan.current_index == 0

    def test_teaching_mode_accepts_four_values(self):
        for mode in ("didactic", "heuristic", "discussion", "teacher"):
            plan = self._make_plan(teaching_mode=mode)
            assert plan.teaching_mode == mode

    def test_teaching_mode_rejects_invalid(self):
        with pytest.raises(ValidationError, match="teaching_mode"):
            self._make_plan(teaching_mode="invalid")

    def test_teaching_mode_rejects_none(self):
        with pytest.raises(ValidationError):
            CheckpointPlan(
                topic="test",
                teaching_mode=None,  # type: ignore[arg-type]
                checkpoints=[
                    Checkpoint(
                        title="t",
                        key_point="p",
                        checkpoint_question="q",
                    )
                ],
            )

    def test_checkpoints_min_length(self):
        with pytest.raises(ValidationError):
            CheckpointPlan(
                topic="test",
                teaching_mode="heuristic",
                checkpoints=[],
            )

    def test_current_index_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            self._make_plan(current_index=-1)

    def test_plan_json_round_trip(self):
        """CheckpointPlan JSON 序列化/反序列化往返。"""
        plan = self._make_plan(
            teaching_mode="teacher",
            current_index=2,
            checkpoints=[
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str, bool",
                    checkpoint_question="Python 有哪些基本数据类型?",
                    state=CheckpointState.COMPLETE,
                ),
                Checkpoint(
                    title="条件判断",
                    key_point="if/elif/else, 比较运算符, 逻辑运算符",
                    checkpoint_question="if 和 elif 有什么区别?",
                    state=CheckpointState.TEACHING,
                ),
            ],
        )
        json_str = plan.model_dump_json()
        restored = CheckpointPlan.model_validate_json(json_str)
        assert restored.teaching_mode == "teacher"
        assert restored.current_index == 2
        assert len(restored.checkpoints) == 2
        assert restored.checkpoints[0].state == CheckpointState.COMPLETE
