"""Stack recommendation models."""

from enum import Enum

from pydantic import BaseModel, Field


class MCPTransport(str, Enum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


class LLMRecommendation(BaseModel):
    """Recommended LLM provider and model."""

    provider: str
    model: str
    reason: str


class MCPServerRecommendation(BaseModel):
    """A recommended MCP server."""

    name: str
    transport: MCPTransport
    install: str
    credentials: str = "none"
    description: str = ""


class FrameworkRecommendation(BaseModel):
    """Recommended agent framework (or none)."""

    name: str | None = None
    reason: str = ""


class StackRecommendation(BaseModel):
    """Full stack recommendation from the Recommendation Engine."""

    llm: LLMRecommendation
    framework: FrameworkRecommendation
    mcp_servers: list[MCPServerRecommendation] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    estimated_tokens: int = 0
    estimated_cost: str = "$0.00"
    adjustment_notes: list[str] = Field(
        default_factory=list,
        description="Notes about adjustments made during retry",
    )
