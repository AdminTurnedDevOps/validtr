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

    Returns:
        FinalResult with the best stack recommendation, score, and attempt history.
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

        logger.info("[7/7] Analyzing failures and adjusting stack...")
        adjusted_stack, re_search_hints = retry_ctrl.analyze_and_adjust(stack, score, test_results)

        # If re-search is recommended, run the recommendation engine again
        # with additional context from the failure analysis
        if re_search_hints:
            logger.info("Re-searching with hints: %s", re_search_hints)
            supplemental = await recommender.search_additional(
                task_def, re_search_hints
            )
            # Merge any new MCP servers into the adjusted stack
            existing_names = {s.name for s in adjusted_stack.mcp_servers}
            for server in supplemental:
                if server.name not in existing_names:
                    adjusted_stack.mcp_servers.append(server)
                    adjusted_stack.adjustment_notes.append(
                        f"added MCP server: {server.name} ({server.description})"
                    )
                    logger.info("Added MCP server: %s", server.name)

        stack = adjusted_stack

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
        "Run %s complete: best stack=%s/%s, score=%.1f, attempts=%d",
        run_id,
        best_result.stack.provider,
        best_result.stack.model,
        best_result.score,
        best_result.total_attempts,
    )

    return best_result
