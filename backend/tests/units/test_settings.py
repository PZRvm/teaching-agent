"""core.settings 单元测试."""

from unittest.mock import mock_open, patch
from zoneinfo import ZoneInfo

import pytest
import yaml


class TestLoadYaml:
    """_load_yaml 函数测试."""

    def test_load_yaml_parses_valid_config(self):
        """测试加载有效的 YAML 配置文件."""
        from core.settings import _load_yaml

        fake_config = {"app": {"timezone": "UTC"}}
        m = mock_open(read_data=yaml.dump(fake_config).encode("utf-8"))

        with patch("builtins.open", m):
            result = _load_yaml("app.yml")

        assert result == fake_config

    def test_load_yaml_raises_on_empty_file(self):
        """测试空 YAML 文件抛出 ValueError."""
        from core.settings import _load_yaml

        m = mock_open(read_data="")

        with patch("builtins.open", m), pytest.raises(ValueError, match="为空或格式无效"):
            _load_yaml("empty.yml")

    def test_load_yaml_raises_on_missing_file(self):
        """测试不存在的文件抛出 FileNotFoundError."""
        from core.settings import _load_yaml

        with pytest.raises(FileNotFoundError):
            _load_yaml("nonexistent.yml")

    def test_load_yaml_uses_utf8_encoding(self):
        """测试使用 UTF-8 编码读取文件."""
        from core.settings import _load_yaml

        fake_config = {"key": "值"}
        m = mock_open(read_data=yaml.dump(fake_config).encode("utf-8"))

        with patch("builtins.open", m) as mock_file:
            _load_yaml("test.yml")
            _, kwargs = mock_file.call_args
            assert kwargs.get("encoding") == "utf-8"


class TestTimezoneConfig:
    """时区配置测试."""

    def test_timezone_is_zoneinfo_instance(self):
        """测试 TIMEZONE 是 ZoneInfo 实例."""
        from core.settings import TIMEZONE

        assert isinstance(TIMEZONE, ZoneInfo)

    def test_timezone_value(self):
        """测试 TIMEZONE 为 Asia/Shanghai."""
        from core.settings import TIMEZONE

        assert str(TIMEZONE) == "Asia/Shanghai"


class TestTeachingTemperatures:
    """教学温度配置测试."""

    def test_teaching_temperatures_has_expected_keys(self):
        """测试包含所有教学模式."""
        from core.settings import TEACHING_TEMPERATURES

        assert "didactic" in TEACHING_TEMPERATURES
        assert "heuristic" in TEACHING_TEMPERATURES
        assert "discussion" in TEACHING_TEMPERATURES

    def test_teaching_temperatures_values_are_float(self):
        """测试温度值为浮点数."""
        from core.settings import TEACHING_TEMPERATURES

        for mode, temp in TEACHING_TEMPERATURES.items():
            assert isinstance(temp, float), f"{mode} 的温度值不是浮点数"

    def test_teaching_temperatures_didactic_is_lowest(self):
        """测试灌输式温度最低（更确定性的回答）."""
        from core.settings import TEACHING_TEMPERATURES

        assert TEACHING_TEMPERATURES["didactic"] < TEACHING_TEMPERATURES["discussion"]

    def test_teaching_temperatures_values(self):
        """测试温度值符合预期."""
        from core.settings import TEACHING_TEMPERATURES

        assert TEACHING_TEMPERATURES["didactic"] == 0.3
        assert TEACHING_TEMPERATURES["heuristic"] == 0.5
        assert TEACHING_TEMPERATURES["discussion"] == 0.7


class TestStudentRespondProbabilities:
    """学生响应概率配置测试."""

    def test_student_respond_probabilities_has_expected_keys(self):
        """测试包含所有态度类型."""
        from core.settings import STUDENT_RESPOND_PROBABILITIES

        assert "active" in STUDENT_RESPOND_PROBABILITIES
        assert "neutral" in STUDENT_RESPOND_PROBABILITIES
        assert "passive" in STUDENT_RESPOND_PROBABILITIES

    def test_student_respond_probabilities_values_are_float(self):
        """测试概率值为浮点数."""
        from core.settings import STUDENT_RESPOND_PROBABILITIES

        for attitude, prob in STUDENT_RESPOND_PROBABILITIES.items():
            assert isinstance(prob, float), f"{attitude} 的概率值不是浮点数"

    def test_student_respond_probabilities_values(self):
        """测试概率值符合预期."""
        from core.settings import STUDENT_RESPOND_PROBABILITIES

        assert STUDENT_RESPOND_PROBABILITIES["active"] == 0.8
        assert STUDENT_RESPOND_PROBABILITIES["neutral"] == 0.5
        assert STUDENT_RESPOND_PROBABILITIES["passive"] == 0.2

    def test_student_respond_probabilities_active_highest(self):
        """测试积极学生响应概率最高."""
        from core.settings import STUDENT_RESPOND_PROBABILITIES

        assert (
            STUDENT_RESPOND_PROBABILITIES["active"]
            > STUDENT_RESPOND_PROBABILITIES["neutral"]
            > STUDENT_RESPOND_PROBABILITIES["passive"]
        )
