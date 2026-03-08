"""Retry Controller — manages retry logic when score < threshold."""

import logging

from models.score import AttemptResult, ScoreResult, StackSummary
from models.stack import StackRecommendation
from models.test_result import TestSuiteResult
from retry.analysis import analyze_failures, apply_adjustments

logger = logging.getLogger(__name__)


class RetryController:
    """Decides whether to retry and how to adjust the stack."""

    def __init__(self, max_retries: int = 3, threshold: float = 95.0):
        self.max_retries = max_retries
        self.threshold = threshold
        self.attempts: list[AttemptResult] = []

    def should_retry(self, score: ScoreResult, attempt_number: int) -> bool:
        """Determine if we should retry based on score and attempt count."""
        if score.composite_score >= self.threshold:
            logger.info("Score %.1f >= threshold %.1f, no retry needed", score.composite_score, self.threshold)
            return False

        if attempt_number >= self.max_retries:
            logger.info("Max retries (%d) reached", self.max_retries)
            return False

        logger.info(
            "Score %.1f < threshold %.1f, will retry (attempt %d/%d)",
            score.composite_score,
            self.threshold,
            attempt_number,
            self.max_retries,
        )
        return True

    def get_adjusted_stack(
        self,
        current_stack: StackRecommendation,
        score: ScoreResult,
        test_results: TestSuiteResult,
    ) -> StackRecommendation:
        """Generate an adjusted stack recommendation for retry."""
        adjustments = analyze_failures(score, test_results, current_stack)
        logger.info("Adjustments for retry: %s", adjustments)
        return apply_adjustments(current_stack, adjustments)

    def record_attempt(
        self,
        attempt_number: int,
        score: ScoreResult,
        artifacts: dict[str, str],
        stack: StackRecommendation | None = None,
        test_code: str = "",
        adjustment_notes: list[str] | None = None,
    ) -> None:
        """Record an attempt result."""
        stack_summary = StackSummary()
        if stack:
            stack_summary = StackSummary(
                provider=stack.llm.provider,
                model=stack.llm.model,
                framework=stack.framework.name,
                mcp_servers=[s.name for s in stack.mcp_servers],
                adjustment_notes=stack.adjustment_notes,
            )
        self.attempts.append(AttemptResult(
            attempt_number=attempt_number,
            score=score,
            stack=stack_summary,
            artifacts=artifacts,
            test_code=test_code,
            adjustment_notes=adjustment_notes or [],
        ))

    def get_best_attempt(self) -> AttemptResult | None:
        """Return the best-scoring attempt."""
        if not self.attempts:
            return None
        return max(self.attempts, key=lambda a: a.score.composite_score)
