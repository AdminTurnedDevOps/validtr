"""Failure analysis for retry decisions."""

import logging

from models.score import ScoreResult
from models.stack import StackRecommendation
from models.test_result import TestSuiteResult, TestStatus

logger = logging.getLogger(__name__)

# Model upgrade paths
MODEL_UPGRADES = {
    "anthropic": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
    "openai": ["gpt-4o-mini", "gpt-4o", "o3"],
    "gemini": ["gemini-2.5-flash", "gemini-2.5-pro"],
}


def analyze_failures(
    score: ScoreResult,
    test_results: TestSuiteResult,
    current_stack: StackRecommendation,
) -> list[str]:
    """Analyze failures and return a list of adjustment recommendations."""
    adjustments = []

    # Find weakest dimensions
    dimensions_by_score = sorted(score.dimensions, key=lambda d: d.score / d.max_score if d.max_score > 0 else 1)

    for dim in dimensions_by_score:
        ratio = dim.score / dim.max_score if dim.max_score > 0 else 1
        if ratio >= 0.95:
            continue

        if dim.name == "Test passing":
            # Check what kinds of tests failed
            failed_tests = [t for t in test_results.tests if t.status == TestStatus.FAILED]
            if failed_tests:
                adjustments.append(f"upgrade_model: {len(failed_tests)} tests failed")

        elif dim.name == "Execution":
            adjustments.append("check_dependencies: execution failure")

        elif dim.name == "Syntax validity":
            adjustments.append("upgrade_model: syntax errors in output")

        elif dim.name == "Completeness":
            adjustments.append("upgrade_model: incomplete output")
            adjustments.append("add_mcp_server: may need additional tools")

    if not adjustments:
        adjustments.append("upgrade_model: general improvement needed")

    return adjustments


def apply_adjustments(
    stack: StackRecommendation,
    adjustments: list[str],
) -> StackRecommendation:
    """Apply adjustments to the stack recommendation for retry."""
    new_stack = stack.model_copy(deep=True)
    new_stack.adjustment_notes = adjustments

    for adj in adjustments:
        action = adj.split(":")[0].strip()

        if action == "upgrade_model":
            # Try to upgrade to a stronger model
            provider = new_stack.llm.provider
            models = MODEL_UPGRADES.get(provider, [])
            current_idx = -1
            for i, m in enumerate(models):
                if m == new_stack.llm.model:
                    current_idx = i
                    break

            if current_idx < len(models) - 1:
                new_model = models[current_idx + 1]
                logger.info("Upgrading model: %s -> %s", new_stack.llm.model, new_model)
                new_stack.llm.model = new_model
                new_stack.llm.reason = f"Upgraded from previous attempt: {adj}"

    return new_stack
