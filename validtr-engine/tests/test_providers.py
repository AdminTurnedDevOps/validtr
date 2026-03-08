"""Tests for provider factory and provider classes."""

import pytest

from providers.base import LLMProvider, get_provider


class TestGetProvider:
    """Tests for the get_provider() factory function."""

    def test_returns_anthropic_provider(self):
        provider = get_provider("anthropic", api_key="fake-key")
        assert provider.provider_name == "anthropic"
        assert isinstance(provider, LLMProvider)

    def test_returns_openai_provider(self):
        provider = get_provider("openai", api_key="fake-key")
        assert provider.provider_name == "openai"
        assert isinstance(provider, LLMProvider)

    def test_returns_gemini_provider(self):
        provider = get_provider("gemini", api_key="fake-key")
        assert provider.provider_name == "gemini"
        assert isinstance(provider, LLMProvider)

    def test_raises_for_unknown_provider(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("llama", api_key="fake-key")

    def test_raises_for_empty_provider(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("", api_key="fake-key")


class TestAnthropicProvider:
    """Tests for AnthropicProvider attributes."""

    def test_default_model(self):
        provider = get_provider("anthropic", api_key="fake-key")
        assert provider.default_model == "claude-sonnet-4-20250514"

    def test_provider_name(self):
        provider = get_provider("anthropic", api_key="fake-key")
        assert provider.provider_name == "anthropic"

    def test_custom_model(self):
        provider = get_provider("anthropic", api_key="fake-key", model="claude-opus-4-20250514")
        assert provider.model == "claude-opus-4-20250514"

    def test_default_model_when_none(self):
        provider = get_provider("anthropic", api_key="fake-key", model=None)
        assert provider.model == "claude-sonnet-4-20250514"


class TestOpenAIProvider:
    """Tests for OpenAIProvider attributes."""

    def test_default_model(self):
        provider = get_provider("openai", api_key="fake-key")
        assert provider.default_model == "gpt-4o"

    def test_provider_name(self):
        provider = get_provider("openai", api_key="fake-key")
        assert provider.provider_name == "openai"

    def test_custom_model(self):
        provider = get_provider("openai", api_key="fake-key", model="gpt-4o-mini")
        assert provider.model == "gpt-4o-mini"


class TestGeminiProvider:
    """Tests for GeminiProvider attributes."""

    def test_default_model(self):
        provider = get_provider("gemini", api_key="fake-key")
        assert provider.default_model == "gemini-2.5-flash"

    def test_provider_name(self):
        provider = get_provider("gemini", api_key="fake-key")
        assert provider.provider_name == "gemini"

    def test_custom_model(self):
        provider = get_provider("gemini", api_key="fake-key", model="gemini-2.5-pro")
        assert provider.model == "gemini-2.5-pro"
