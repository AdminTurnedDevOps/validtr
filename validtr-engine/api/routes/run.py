"""Run task API routes."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from analyzer.task_analyzer import TaskAnalyzer
from orchestrator import run_task
from providers.base import get_provider
from recommender.engine import RecommendationEngine

logger = logging.getLogger(__name__)
router = APIRouter()


class RunRequest(BaseModel):
    task: str
    provider: str = "anthropic"
    model: str | None = None
    api_key: str | None = None
    search_api_key: str | None = None
    max_retries: int = 3
    score_threshold: float = 95.0
    timeout: int = 300
    dry_run: bool = False


class RunResponse(BaseModel):
    run_id: str
    score: float
    passed: bool
    total_attempts: int
    artifact_count: int
    artifacts: dict[str, str]


@router.post("/run")
async def api_run_task(req: RunRequest):
    """Run the full validtr pipeline for a task."""
    # Validate provider early to return 400 instead of 500
    valid_providers = {"anthropic", "openai", "gemini"}
    if req.provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {req.provider}. Choose from: {sorted(valid_providers)}",
        )

    if req.dry_run:
        return await _dry_run(req)

    try:
        result = await run_task(
            task=req.task,
            provider=req.provider,
            model=req.model,
            api_key=req.api_key,
            search_api_key=req.search_api_key,
            max_retries=req.max_retries,
            score_threshold=req.score_threshold,
            timeout=req.timeout,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        err_type = type(e).__name__
        if "Authentication" in err_type or "AuthError" in err_type:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {e}") from e
        if "Permission" in err_type or "RateLimit" in err_type:
            raise HTTPException(status_code=429, detail=f"Rate limited or permission denied: {e}") from e
        raise

    return RunResponse(
        run_id=result.run_id,
        score=result.score,
        passed=result.passed,
        total_attempts=result.total_attempts,
        artifact_count=len(result.artifacts),
        artifacts=result.artifacts,
    )


async def _dry_run(req: RunRequest):
    """Recommend a stack without executing."""
    try:
        llm = get_provider(req.provider, api_key=req.api_key or "", model=req.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        analyzer = TaskAnalyzer(provider=llm)
        task_def = await analyzer.analyze(req.task)

        recommender = RecommendationEngine(
            provider=llm,
            search_api_key=req.search_api_key,
        )
        stack = await recommender.recommend(task_def, preferred_provider=req.provider)
    except Exception as e:
        err_type = type(e).__name__
        if "Authentication" in err_type or "AuthError" in err_type:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {e}") from e
        if "Permission" in err_type or "RateLimit" in err_type:
            raise HTTPException(status_code=429, detail=f"Rate limited or permission denied: {e}") from e
        raise

    return {
        "task": task_def.model_dump(),
        "recommendation": stack.model_dump(),
    }
