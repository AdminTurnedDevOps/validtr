"""Safety limits for execution."""

from pydantic import BaseModel


class SafetyLimits(BaseModel):
    """Configurable safety limits for task execution."""

    timeout_seconds: int = 300  # 5 minutes
    max_llm_calls: int = 50
    max_tool_calls: int = 100
