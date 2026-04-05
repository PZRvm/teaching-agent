"""应用配置 — 从 YAML 文件加载配置项."""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


def _load_yaml(filename: str) -> dict:
    """加载 configs/ 下的 YAML 配置文件."""
    config_path = Path(__file__).parents[1] / "configs" / filename
    with open(config_path) as f:
        return yaml.safe_load(f)


_APP = _load_yaml("app.yml")
_LLM = _load_yaml("llm.yml")

# 时区
TIMEZONE = ZoneInfo(_APP["app"]["timezone"])

# 教学模式 → 温度
TEACHING_TEMPERATURES: dict[str, float] = _LLM["teaching_temperatures"]

# 学生态度 → 响应概率
STUDENT_RESPOND_PROBABILITIES: dict[str, float] = _LLM["student_respond_probabilities"]
