"""会话级别的记忆管理."""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas import Message


@dataclass
class SessionMemory:
    """会话级别的记忆管理."""

    session_id: int
    topic: str

    message_history: list[Message] = field(default_factory=list)
    teaching_summary: str = ""
    checkpoint_summaries: list[str] = field(default_factory=list)

    max_history_messages: int = 50
    summary_update_interval: int = 10
    last_summary_update: int = 0

    def add_message(self, message: Message) -> None:
        """添加消息到历史."""
        self.message_history.append(message)

    def should_update_summary(self) -> bool:
        """判断是否需要更新摘要."""
        return len(self.message_history) - self.last_summary_update >= self.summary_update_interval

    def mark_summary_updated(self) -> None:
        """标记摘要已更新."""
        self.last_summary_update = len(self.message_history)

    def clear_message_history(self) -> None:
        """清除消息历史（检查点边界调用）.

        同时将 last_summary_update 设为 0，因为新的检查点
        消息计数从 0 开始。
        """
        self.message_history.clear()
        self.last_summary_update = 0

    def get_recent_messages(self) -> list[Message]:
        """获取最近 N 条消息."""
        return self.message_history[-self.max_history_messages :]

    def get_agent_context(self, max_recent_messages: int | None = None) -> str:
        """获取 agent 上下文.

        Args:
            max_recent_messages: 最多包含的最近消息条数，None 表示使用 max_history_messages
        """
        if max_recent_messages is not None:
            recent = self.message_history[-max_recent_messages:]
        else:
            recent = self.get_recent_messages()
        parts = [
            f"教学主题: {self.topic}",
            f"教学摘要: {self.teaching_summary}",
            "最近的对话:",
        ]
        for msg in recent:
            parts.append(f"[{msg.sender}] ({msg.message_type.value}): {msg.content}")
        return "\n".join(parts)

    def get_full_context(self) -> str:
        """获取完整上下文（包含所有检查点摘要）.

        用于最终总结等需要全局视角的场景。
        包含 teaching_summary（如果有）和所有 checkpoint_summaries。
        """
        parts = [f"教学主题: {self.topic}"]
        if self.teaching_summary:
            parts.append(f"教学摘要: {self.teaching_summary}")
        if self.checkpoint_summaries:
            parts.append("各检查点教学摘要:")
            for i, summary in enumerate(self.checkpoint_summaries, 1):
                parts.append(f"  检查点{i}: {summary}")
        parts.append("最近的对话:")
        for msg in self.message_history[-self.max_history_messages:]:
            parts.append(f"[{msg.sender}] ({msg.message_type.value}): {msg.content}")
        return "\n".join(parts)
