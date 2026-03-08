"""Scoring models."""

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """Score for a single dimension."""

    name: str
    score: float
    max_score: float
    details: str = ""


class ScoreResult(BaseModel):
    """Composite score from the Scoring Engine."""

    composite_score: float = 0.0
    dimensions: list[DimensionScore] = Field(default_factory=list)
    passed: bool = False
    threshold: float = 95.0

    def check_passed(self) -> bool:
        self.passed = self.composite_score >= self.threshold
        return self.passed


class StackSummary(BaseModel):
    """Lightweight summary of the stack used for an attempt."""

    provider: str = ""
    model: str = ""
    framework: str | None = None
    mcp_servers: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    prompt_strategy: str = ""
    adjustment_notes: list[str] = Field(default_factory=list)


class AttemptResult(BaseModel):
    """Result of a single attempt (execution + tests + score)."""

    attempt_number: int
    score: ScoreResult
    stack: StackSummary = Field(default_factory=StackSummary)
    artifacts: dict[str, str] = Field(default_factory=dict)
    test_code: str = ""
    adjustment_notes: list[str] = Field(default_factory=list)


class FinalResult(BaseModel):
    """Final result returned by the orchestrator."""

    run_id: str
    task_description: str
    best_score: float = 0.0
    best_attempt: int = 0
    total_attempts: int = 0
    attempts: list[AttemptResult] = Field(default_factory=list)
    stack: StackSummary = Field(default_factory=StackSummary)
    artifacts: dict[str, str] = Field(default_factory=dict)
    test_results: str = ""
    score: float = 0.0
    passed: bool = False
    total_cost: str = "$0.00"
    total_tokens: int = 0
    total_duration_ms: int = 0
