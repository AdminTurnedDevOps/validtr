"""Credential management for stack provisioning."""

import logging
import os

from models.stack import StackRecommendation

logger = logging.getLogger(__name__)

# Map provider names to their API key environment variables
PROVIDER_KEY_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
}


def resolve_credentials(
    stack: StackRecommendation,
    explicit_keys: dict[str, str] | None = None,
) -> dict[str, str]:
    """Resolve all required credentials for a stack.

    Checks explicit_keys first, then environment variables.
    Returns a dict of env var name -> value to inject into containers.
    """
    explicit_keys = explicit_keys or {}
    credentials: dict[str, str] = {}

    # LLM provider API key
    provider_env_var = PROVIDER_KEY_MAP.get(stack.llm.provider)
    if provider_env_var:
        key = explicit_keys.get(provider_env_var) or os.environ.get(provider_env_var)
        if key:
            credentials[provider_env_var] = key
        else:
            logger.warning("No API key found for provider %s (expected %s)", stack.llm.provider, provider_env_var)

    # MCP server credentials
    for server in stack.mcp_servers:
        if server.credentials != "none":
            cred_value = explicit_keys.get(server.credentials) or os.environ.get(server.credentials)
            if cred_value:
                credentials[server.credentials] = cred_value
            else:
                logger.warning("No credential found for MCP server %s (expected %s)", server.name, server.credentials)

    return credentials


def check_credentials(stack: StackRecommendation, credentials: dict[str, str]) -> list[str]:
    """Check if all required credentials are present. Returns list of missing ones."""
    missing = []

    provider_env_var = PROVIDER_KEY_MAP.get(stack.llm.provider)
    if provider_env_var and provider_env_var not in credentials:
        missing.append(provider_env_var)

    for server in stack.mcp_servers:
        if server.credentials != "none" and server.credentials not in credentials:
            missing.append(server.credentials)

    return missing
