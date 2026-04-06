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

    def get_recent_messages(self) -> list[Message]:
        """获取最近 N 条消息."""
        return self.message_history[-self.max_history_messages :]

    def get_agent_context(self) -> str:
        """获取 agent 完整上下文."""
        recent = self.get_recent_messages()
        parts = [
            f"教学主题: {self.topic}",
            f"教学摘要: {self.teaching_summary}",
            "最近的对话:",
        ]
        for msg in recent:
            parts.append(f"[{msg.sender}] ({msg.message_type.value}): {msg.content}")
        return "\n".join(parts)
