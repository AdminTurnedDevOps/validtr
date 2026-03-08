"""Retry Controller — manages retry logic when score < threshold."""

import logging

from models.score import AttemptResult, ScoreResult, StackSummary
from models.stack import StackRecommendation
from models.test_result import TestSuiteResult
from retry.analysis import analyze_failures, apply_adjustments, get_re_search_hints

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

    def analyze_and_adjust(
        self,
        current_stack: StackRecommendation,
        score: ScoreResult,
        test_results: TestSuiteResult,
    ) -> tuple[StackRecommendation, list[str]]:
        """Analyze failures, adjust stack, and return (new_stack, re_search_hints).

        re_search_hints: non-empty if the recommendation engine should re-search
        with additional queries before the next attempt.
        """
        adjustments = analyze_failures(score, test_results, current_stack)
        new_stack = apply_adjustments(current_stack, adjustments)
        re_search_hints = get_re_search_hints(adjustments)
        return new_stack, re_search_hints

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
                skills=stack.skills,
                prompt_strategy=stack.prompt_strategy,
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
