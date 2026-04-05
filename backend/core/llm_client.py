"""LLM 客户端 - 封装 langchain_openai ChatOpenAI."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from langchain_openai import ChatOpenAI


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

    def invoke(
        self,
        prompt: str | list,
        temperature: float | None = None,
    ) -> str:
        """调用 LLM 生成响应.

        Args:
            prompt: 提示文本或消息列表
            temperature: 可选温度覆盖

        Returns:
            LLM 响应文本
        """
        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=prompt)] if isinstance(prompt, str) else prompt

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
            prompt: 提示文本或消息列表
            temperature: 可选温度覆盖

        Yields:
            每个文本 chunk
        """
        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=prompt)] if isinstance(prompt, str) else prompt

        invoke_kwargs: dict = {"input": messages}
        if temperature is not None:
            invoke_kwargs["temperature"] = temperature

        for chunk in self._llm.stream(**invoke_kwargs):
            yield chunk.content
