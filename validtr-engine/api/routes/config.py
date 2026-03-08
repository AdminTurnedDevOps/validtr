"""Configuration API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_config():
    """Get current engine configuration."""
    return {
        "engine_version": "0.1.0",
        "supported_providers": ["anthropic", "openai", "gemini"],
        "supported_task_types": ["code-generation", "infrastructure", "research", "automation"],
    }
