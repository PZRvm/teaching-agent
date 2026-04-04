"""LLM Client 单元测试."""

from unittest.mock import MagicMock, patch


class TestLLMClient:
    """LLM Client 测试."""

    def test_init_uses_config(self):
        """测试使用配置初始化."""
        from core.llm_client import LLMClient

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
            temperature=0.5,
            max_tokens=1000,
        )

        assert client.model == "test-model"
        assert client.temperature == 0.5
        assert client.max_tokens == 1000

    def test_init_from_config_uses_env_api_key(self):
        """测试 from_config() 从 .env 读取 API key."""
        from core.llm_client import LLMClient

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-env-key"}):
            client = LLMClient.from_config()

        assert client.api_key == "test-env-key"
        assert client.base_url == "https://api.siliconflow.cn/v1"
        assert client.model == "Qwen/Qwen2.5-7B-Instruct"

    def test_init_from_config_raises_without_api_key(self):
        """测试 from_config() 在无 API key 时抛出 ValueError."""
        import pytest

        from core.llm_client import LLMClient

        with patch.dict("os.environ", {}, clear=True), pytest.raises(ValueError, match="OPENAI_API_KEY"):
            LLMClient.from_config()

    @patch("core.llm_client.ChatOpenAI")
    def test_invoke_returns_response(self, mock_chat_openai_cls):
        """测试 invoke 调用 LLM 并返回响应."""
        from core.llm_client import LLMClient

        mock_llm_instance = MagicMock()
        mock_chat_openai_cls.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = MagicMock(content="这是讲授内容")

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
        )

        result = client.invoke("请讲授Python变量")

        assert result == "这是讲授内容"

    @patch("core.llm_client.ChatOpenAI")
    def test_invoke_with_messages(self, mock_chat_openai_cls):
        """测试 invoke 传入消息列表."""
        from langchain_core.messages import HumanMessage, SystemMessage

        from core.llm_client import LLMClient

        mock_llm_instance = MagicMock()
        mock_chat_openai_cls.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = MagicMock(content="响应内容")

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
        )

        messages = [
            SystemMessage(content="你是教师"),
            HumanMessage(content="请讲授变量"),
        ]
        result = client.invoke(messages)

        assert result == "响应内容"

    @patch("core.llm_client.ChatOpenAI")
    def test_invoke_with_temperature_override(self, mock_chat_openai_cls):
        """测试 invoke 支持临时覆盖 temperature."""
        from core.llm_client import LLMClient

        mock_llm_instance = MagicMock()
        mock_chat_openai_cls.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value = MagicMock(content="响应")

        client = LLMClient(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
            temperature=0.7,
        )

        client.invoke("test", temperature=0.1)

        mock_llm_instance.invoke.assert_called_once()
        call_kwargs = mock_llm_instance.invoke.call_args
        assert call_kwargs[1].get("temperature") == 0.1
