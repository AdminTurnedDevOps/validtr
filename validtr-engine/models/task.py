"""Task definition models."""

from enum import Enum

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    CODE_GENERATION = "code-generation"
    INFRASTRUCTURE = "infrastructure"
    RESEARCH = "research"
    AUTOMATION = "automation"


class Complexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class TaskRequirements(BaseModel):
    """Extracted requirements from the task description."""

    language: str | None = None
    frameworks: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class TaskDefinition(BaseModel):
    """Structured output from the Task Analyzer."""

    id: str
    raw_input: str
    type: TaskType
    domain: str
    requirements: TaskRequirements
    complexity: Complexity
    success_criteria: list[str] = Field(default_factory=list)
    testable_assertions: list[str] = Field(default_factory=list)
