"""core.llm_utils 单元测试."""

from unittest.mock import MagicMock

import pytest

from core.llm_utils import safe_llm_call


class TestSafeLlmCall:
    """safe_llm_call 函数测试."""

    def test_returns_result_on_success(self):
        """测试成功调用返回结果."""
        fn = MagicMock(return_value="hello")
        result = safe_llm_call(fn, "教师", "讲授", ["msg"])
        assert result == "hello"
        fn.assert_called_once_with(["msg"])

    def test_passes_kwargs_to_fn(self):
        """测试关键字参数正确传递."""
        fn = MagicMock(return_value="ok")
        result = safe_llm_call(fn, "教师", "讲授", ["msg"], temperature=0.5)
        assert result == "ok"
        fn.assert_called_once_with(["msg"], temperature=0.5)

    def test_raises_runtime_error_on_failure(self):
        """测试异常时抛出 RuntimeError."""
        fn = MagicMock(side_effect=ConnectionError("API timeout"))
        with pytest.raises(RuntimeError, match="教师.*讲授.*失败"):
            safe_llm_call(fn, "教师", "讲授", ["msg"])

    def test_chains_original_exception(self):
        """测试原始异常通过 __cause__ 链接."""
        original = ConnectionError("API timeout")
        fn = MagicMock(side_effect=original)
        with pytest.raises(RuntimeError) as exc_info:
            safe_llm_call(fn, "教师", "讲授", ["msg"])
        assert exc_info.value.__cause__ is original

    def test_error_message_includes_caller_and_description(self):
        """测试错误消息包含调用者和描述."""
        fn = MagicMock(side_effect=ValueError("bad"))
        with pytest.raises(RuntimeError) as exc_info:
            safe_llm_call(fn, "学生 张三", "回答问题", "prompt")
        assert "学生 张三" in str(exc_info.value)
        assert "回答问题" in str(exc_info.value)
