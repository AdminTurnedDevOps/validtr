"""Test result models."""

from enum import Enum

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class SingleTestResult(BaseModel):
    """Result of a single test case."""

    name: str
    status: TestStatus
    message: str = ""
    duration_ms: int = 0


class TestSuiteResult(BaseModel):
    """Aggregated result from running all generated tests."""

    tests: list[SingleTestResult] = Field(default_factory=list)
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    test_code: str = ""
    runner_output: str = ""

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total
