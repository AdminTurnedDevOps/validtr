"""Top-level orchestrator — chains all components into the full pipeline."""

import logging
import uuid

from analyzer.task_analyzer import TaskAnalyzer
from executor.engine import ExecutionEngine
from executor.safety import SafetyLimits
from models.score import FinalResult, StackSummary
from providers.base import get_provider
from recommender.engine import RecommendationEngine
from retry.controller import RetryController
from scorer.engine import ScoringEngine
from test_generator.engine import TestGenerator

logger = logging.getLogger(__name__)


async def run_task(
    task: str,
    provider: str = "anthropic",
    api_key: str | None = None,
    model: str | None = None,
    max_retries: int = 3,
    score_threshold: float = 95.0,
    timeout: int = 300,
    search_api_key: str | None = None,
    extra_api_keys: dict[str, str] | None = None,
) -> FinalResult:
    """Run the full validtr pipeline for a task.

    This is the main entry point for Phase 1.

    Args:
        task: Natural language task description.
        provider: LLM provider name ("anthropic", "openai", "gemini").
        api_key: API key for the specified provider.
        model: Optional specific model to use.
        max_retries: Maximum retry attempts if score < threshold.
        score_threshold: Minimum score to pass (0-100).
        timeout: Execution timeout in seconds.
        search_api_key: API key for web search (Tavily).
        extra_api_keys: Additional API keys (e.g., for MCP servers).

    Returns:
        FinalResult with score, artifacts, test results, and attempt history.
    """
    run_id = uuid.uuid4().hex[:6]
    logger.info("Starting validtr run %s: %s", run_id, task[:80])

    # Initialize the LLM provider (used for analysis, recommendation, test gen, scoring)
    llm = get_provider(provider, api_key=api_key or "", model=model)

    # Build API keys dict for container injection
    api_keys = dict(extra_api_keys or {})
    if api_key:
        from provisioner.credentials import PROVIDER_KEY_MAP
        env_var = PROVIDER_KEY_MAP.get(provider)
        if env_var:
            api_keys[env_var] = api_key

    # === Step 1: Analyze task ===
    logger.info("[1/7] Analyzing task...")
    analyzer = TaskAnalyzer(provider=llm)
    task_def = await analyzer.analyze(task)
    logger.info("Task type: %s, complexity: %s, %d assertions", task_def.type, task_def.complexity, len(task_def.testable_assertions))

    # === Step 2: Recommend stack ===
    logger.info("[2/7] Generating recommendation...")
    recommender = RecommendationEngine(
        provider=llm,
        search_api_key=search_api_key,
    )
    stack = await recommender.recommend(task_def, preferred_provider=provider)
    logger.info("Recommended: %s/%s", stack.llm.provider, stack.llm.model)

    # Initialize retry controller
    retry_ctrl = RetryController(max_retries=max_retries, threshold=score_threshold)

    # Initialize engines
    executor = ExecutionEngine(safety_limits=SafetyLimits(timeout_seconds=timeout))
    test_gen = TestGenerator(provider=llm)
    scoring = ScoringEngine(provider=llm)

    best_result = None
    attempt = 0

    while True:
        attempt += 1
        logger.info("=== Attempt %d ===", attempt)

        # === Step 3: Provision & Execute ===
        logger.info("[3/7] Provisioning containers...")
        attempt_run_id = f"{run_id}-{attempt}"

        logger.info("[4/7] Executing task...")
        execution = await executor.execute(
            run_id=attempt_run_id,
            task=task_def,
            stack=stack,
            api_keys=api_keys,
        )

        if not execution.success:
            logger.warning("Execution failed: %s", execution.error)

        # === Step 5: Generate & run tests ===
        logger.info("[5/7] Generating tests...")
        test_results = await test_gen.generate_and_run(task_def, execution)
        logger.info("Tests: %d/%d passed", test_results.passed, test_results.total)

        # === Step 6: Score ===
        logger.info("[6/7] Scoring...")
        score = await scoring.score(task_def, execution, test_results, score_threshold)
        logger.info("Score: %.1f/100", score.composite_score)

        # Record attempt
        retry_ctrl.record_attempt(
            attempt_number=attempt,
            score=score,
            artifacts=execution.artifacts,
            stack=stack,
            test_code=test_results.test_code,
            adjustment_notes=stack.adjustment_notes,
        )

        # === Step 7: Retry? ===
        if not retry_ctrl.should_retry(score, attempt):
            break

        logger.info("[7/7] Adjusting stack for retry...")
        stack = retry_ctrl.get_adjusted_stack(stack, score, test_results)

    # Get best result
    best = retry_ctrl.get_best_attempt()
    if best:
        best_result = FinalResult(
            run_id=run_id,
            task_description=task,
            best_score=best.score.composite_score,
            best_attempt=best.attempt_number,
            total_attempts=len(retry_ctrl.attempts),
            attempts=retry_ctrl.attempts,
            stack=best.stack,
            artifacts=best.artifacts,
            test_results=best.test_code,
            score=best.score.composite_score,
            passed=best.score.passed,
        )
    else:
        best_result = FinalResult(
            run_id=run_id,
            task_description=task,
        )

    logger.info(
        "Run %s complete: score=%.1f, attempts=%d, passed=%s",
        run_id,
        best_result.score,
        best_result.total_attempts,
        best_result.passed,
    )

    return best_result
