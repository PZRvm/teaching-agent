"""应用配置 — 从 YAML 文件加载配置项."""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


def _load_yaml(filename: str) -> dict:
    """加载 configs/ 下的 YAML 配置文件."""
    config_path = Path(__file__).parents[1] / "configs" / filename
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if config is None:
        raise ValueError(f"配置文件 {filename} 为空或格式无效")
    return config


_APP = _load_yaml("app.yml")
_LLM = _load_yaml("llm.yml")

# 时区
TIMEZONE = ZoneInfo(_APP["app"]["timezone"])

# 教学模式 → 温度
TEACHING_TEMPERATURES: dict[str, float] = _LLM["teaching_temperatures"]

# 默认温度（教学模式未匹配时）
DEFAULT_TEACHING_TEMPERATURE: float = 0.3

# 内容完成度判断温度（需要高确定性）
CONTENT_JUDGE_TEMPERATURE: float = 0.1

# 学生态度 → 响应概率
STUDENT_RESPOND_PROBABILITIES: dict[str, float] = _LLM["student_respond_probabilities"]

# 默认响应概率（态度未匹配时）
DEFAULT_RESPOND_PROBABILITY: float = 0.5
