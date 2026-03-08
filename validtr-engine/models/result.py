"""Execution result models."""

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool call made during execution."""

    tool_name: str
    arguments: dict = Field(default_factory=dict)
    result: str = ""
    duration_ms: int = 0


class LLMCall(BaseModel):
    """A single LLM API call made during execution."""

    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0


class ExecutionTrace(BaseModel):
    """Full trace of an execution run."""

    llm_calls: list[LLMCall] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    total_tokens: int = 0
    total_duration_ms: int = 0
    error: str | None = None


class ExecutionResult(BaseModel):
    """Output from the Execution Engine."""

    run_id: str
    artifacts: dict[str, str] = Field(
        default_factory=dict,
        description="Map of filename to content for generated artifacts",
    )
    trace: ExecutionTrace = Field(default_factory=ExecutionTrace)
    output_dir: str = ""
    success: bool = True
    error: str | None = None
