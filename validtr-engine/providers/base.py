"""Abstract base class for LLM providers."""

import abc
from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class Message:
    """A chat message."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict] | None = None


@dataclass
class ToolDefinition:
    """Definition of a tool the LLM can call."""

    name: str
    description: str
    parameters: dict  # JSON Schema


class CompletionResponse(BaseModel):
    """Unified response from any LLM provider."""

    content: str = ""
    tool_calls: list[dict] = []
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    stop_reason: str = ""


class LLMProvider(abc.ABC):
    """Abstract base for LLM providers."""

    def __init__(self, api_key: str, model: str | None = None):
        self.api_key = api_key
        self.model = model or self.default_model

    @property
    @abc.abstractmethod
    def default_model(self) -> str: ...

    @property
    @abc.abstractmethod
    def provider_name(self) -> str: ...

    @abc.abstractmethod
    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> CompletionResponse:
        """Send a chat completion request."""
        ...

    async def complete_json(
        self,
        messages: list[Message],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> CompletionResponse:
        """Convenience method for JSON mode completions."""
        return await self.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )


def get_provider(provider_name: str, api_key: str, model: str | None = None) -> LLMProvider:
    """Factory function to get a provider by name."""
    from providers.anthropic import AnthropicProvider
    from providers.gemini import GeminiProvider
    from providers.openai import OpenAIProvider

    providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Choose from: {list(providers.keys())}")
    return providers[provider_name](api_key=api_key, model=model)
