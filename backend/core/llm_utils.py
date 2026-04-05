"""LLM 调用工具函数."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def safe_llm_call[T](
    fn,
    caller: str,
    description: str,
    /,
    *args: object,
    **kwargs: object,
) -> T:
    """包装 LLM 调用，统一错误处理.

    Args:
        fn: LLM 调用函数（如 llm.invoke 或 llm.stream）
        caller: 调用者标识（用于错误日志）
        description: 操作描述（用于错误消息）
        *args: 传递给 fn 的位置参数
        **kwargs: 传递给 fn 的关键字参数

    Returns:
        LLM 调用结果

    Raises:
        RuntimeError: LLM 调用失败时
    """
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.error("%s %s失败: error=%s", caller, description, e)
        raise RuntimeError(f"{caller} {description}失败: {e}") from e
