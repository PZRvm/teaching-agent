"""LLM 客户端 - 封装 langchain_openai ChatOpenAI."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

# 模型上下文窗口限制和消息数量配置
#
# Qwen2.5 模型上下文窗口：
# - Qwen2.5-7B-Instruct: 32,768 tokens
# - Qwen2.5-72B-Instruct: 131,072 tokens
#
# 根据实际测试经验（中文对话）：
# - 7B 模型：50 条消息 → 33000+ tokens (超出限制)
# - 7B 模型：10 条消息 → 约 5000-8000 tokens (安全范围)
# - 72B 模型：由于上下文窗口更大（128K），可保留更多消息
#
# 配置说明：
# - context_limit: 最大输入 token 数（保守估计，留空间给响应）
# - max_messages: 最大保留的非系统消息数量
MODEL_CONTEXT_LIMITS = {
    "qwen2.5-72b-instruct": {"context_limit": 50000, "max_messages": 50},
    "qwen2.5-7b-instruct": {"context_limit": 8000, "max_messages": 10},
    "default": {"context_limit": 5000, "max_messages": 10},
}


class LLMClient:
    """可复用的 LLM 客户端."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> None:
        """初始化 LLM 客户端.

        Args:
            base_url: API 地址
            api_key: API 密钥
            model: 模型名称
            temperature: 采样温度
            max_tokens: 最大 token 数
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm = ChatOpenAI(
            base_url=base_url,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    @classmethod
    def from_config(cls) -> LLMClient:
        """从 .env 和 YAML 配置文件创建实例.

        API key 从 .env 环境变量 OPENAI_API_KEY 读取，
        其余参数从 configs/llm.yml 读取。

        Returns:
            LLMClient 实例
        """
        config_path = Path(__file__).parents[1] / "configs" / "llm.yml"
        with open(config_path) as f:
            llm_config = yaml.safe_load(f)

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError(
                "未设置 OPENAI_API_KEY 环境变量。请在 .env 文件中配置 OPENAI_API_KEY=your_api_key"
            )

        return cls(
            base_url=llm_config["llm"]["base_url"],
            api_key=api_key,
            model=llm_config["llm"]["model"],
            temperature=llm_config["llm"]["temperature"],
            max_tokens=llm_config["llm"]["max_tokens"],
        )

    def _get_model_config(self) -> dict:
        """获取当前模型的配置.

        Returns:
            包含 context_limit 和 max_messages 的配置字典
        """
        model_name = self.model.lower()
        for key, config in MODEL_CONTEXT_LIMITS.items():
            if key in model_name:
                return config
        return MODEL_CONTEXT_LIMITS["default"]

    def _get_context_limit(self) -> int:
        """获取当前模型的上下文窗口限制.

        Returns:
            最大输入 token 数
        """
        return self._get_model_config()["context_limit"]

    def _get_max_messages(self) -> int:
        """获取当前模型允许的最大非系统消息数量.

        Returns:
            最大非系统消息数量
        """
        return self._get_model_config()["max_messages"]

    def _truncate_messages_to_fit(self, messages: list) -> list:
        """截断消息列表以适应上下文窗口.

        使用消息数量限制而非字符估算，更加可靠。
        优先保留系统消息和最近的对话。
        根据当前模型动态调整消息数量限制。

        Args:
            messages: langchain 消息列表

        Returns:
            截断后的消息列表
        """

        # 根据当前模型获取最大非系统消息数量
        max_non_system_messages = self._get_max_messages()

        # 分离系统消息和非系统消息
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        non_system_messages = [m for m in messages if not isinstance(m, SystemMessage)]

        # 保留最近的 N 条非系统消息
        if len(non_system_messages) > max_non_system_messages:
            truncated_non_system = non_system_messages[-max_non_system_messages:]
        else:
            truncated_non_system = non_system_messages

        # 合并系统消息和截断后的非系统消息
        result = system_messages + truncated_non_system

        return result

    def invoke(
        self,
        prompt: str | list,
        temperature: float | None = None,
    ) -> str:
        """调用 LLM 生成响应.

        Args:
            prompt: 提示文本或消息列表（支持 dict 格式 [{"role": "system/user/assistant", "content": "..."}]）
            temperature: 可选温度覆盖

        Returns:
            LLM 响应文本
        """
        from langchain_core.messages import AIMessage, HumanMessage

        # 转换为 langchain 消息格式
        if isinstance(prompt, str):
            messages = [HumanMessage(content=prompt)]
        elif isinstance(prompt, list) and prompt:
            # 检查是否为 dict 格式消息 [{"role": "system", "content": "..."}]
            if isinstance(prompt[0], dict):
                # 转换 dict 格式为 langchain 消息
                role_to_message = {
                    "system": SystemMessage,
                    "user": HumanMessage,
                    "assistant": AIMessage,
                }
                messages = []
                for msg_dict in prompt:
                    role = msg_dict.get("role", "user")
                    content = msg_dict.get("content", "")
                    msg_class = role_to_message.get(role, HumanMessage)
                    messages.append(msg_class(content=content))
            else:
                messages = prompt  # 假设已经是 langchain 消息格式
        else:
            messages = [HumanMessage(content="")]

        # 截断消息以适应上下文窗口
        messages = self._truncate_messages_to_fit(messages)

        invoke_kwargs: dict = {"input": messages}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature

        response = self._llm.invoke(**invoke_kwargs)
        return response.content

    def stream(
        self,
        prompt: str | list,
        temperature: float | None = None,
    ):
        """流式调用 LLM，逐 token 生成响应.

        Args:
            prompt: 提示文本或消息列表（支持 dict 格式 [{"role": "system/user/assistant", "content": "..."}]）
            temperature: 可选温度覆盖

        Yields:
            每个文本 chunk
        """
        from langchain_core.messages import AIMessage, HumanMessage

        # 转换为 langchain 消息格式
        if isinstance(prompt, str):
            messages = [HumanMessage(content=prompt)]
        elif isinstance(prompt, list) and prompt:
            if isinstance(prompt[0], dict):
                role_to_message = {
                    "system": SystemMessage,
                    "user": HumanMessage,
                    "assistant": AIMessage,
                }
                messages = []
                for msg_dict in prompt:
                    role = msg_dict.get("role", "user")
                    content = msg_dict.get("content", "")
                    msg_class = role_to_message.get(role, HumanMessage)
                    messages.append(msg_class(content=content))
            else:
                messages = prompt
        else:
            messages = [HumanMessage(content="")]

        # 截断消息以适应上下文窗口
        messages = self._truncate_messages_to_fit(messages)

        invoke_kwargs: dict = {"input": messages}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature

        for chunk in self._llm.stream(**invoke_kwargs):
            yield chunk.content

    async def ainvoke(
        self,
        prompt: str | list,
        temperature: float | None = None,
    ) -> str:
        """异步调用 LLM 生成响应.

        Args:
            prompt: 提示文本或消息列表（支持 dict 格式 [{"role": "system/user/assistant", "content": "..."}]）
            temperature: 可选温度覆盖

        Returns:
            LLM 响应文本
        """
        from langchain_core.messages import AIMessage, HumanMessage

        # 转换为 langchain 消息格式
        if isinstance(prompt, str):
            messages = [HumanMessage(content=prompt)]
        elif isinstance(prompt, list) and prompt:
            if isinstance(prompt[0], dict):
                role_to_message = {
                    "system": SystemMessage,
                    "user": HumanMessage,
                    "assistant": AIMessage,
                }
                messages = []
                for msg_dict in prompt:
                    role = msg_dict.get("role", "user")
                    content = msg_dict.get("content", "")
                    msg_class = role_to_message.get(role, HumanMessage)
                    messages.append(msg_class(content=content))
            else:
                messages = prompt
        else:
            messages = [HumanMessage(content="")]

        # 截断消息以适应上下文窗口
        messages = self._truncate_messages_to_fit(messages)

        invoke_kwargs: dict = {"input": messages}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature

        response = await self._llm.ainvoke(**invoke_kwargs)
        return response.content
