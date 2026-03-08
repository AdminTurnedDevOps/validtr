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
) -> list[dict]:
    """Analyze failures and return structured adjustment recommendations.

    Each adjustment is a dict: {"action": str, "reason": str, ...}
    """
    adjustments = []

    dimensions_by_score = sorted(
        score.dimensions,
        key=lambda d: d.score / d.max_score if d.max_score > 0 else 1,
    )

    for dim in dimensions_by_score:
        ratio = dim.score / dim.max_score if dim.max_score > 0 else 1
        if ratio >= 0.95:
            continue

        if dim.name == "Test passing":
            failed_tests = [t for t in test_results.tests if t.status == TestStatus.FAILED]
            if failed_tests:
                # Gather failure messages for targeted re-search
                failure_msgs = [t.message for t in failed_tests[:3] if t.message]
                adjustments.append({
                    "action": "upgrade_model",
                    "reason": f"{len(failed_tests)} tests failed",
                })
                if failure_msgs:
                    adjustments.append({
                        "action": "re_search",
                        "reason": "find tools to fix test failures",
                        "query_hints": failure_msgs,
                    })

        elif dim.name == "Execution":
            adjustments.append({
                "action": "add_mcp_server",
                "reason": "execution failure — may need additional tools",
                "query_hints": ["execution runtime tools", current_stack.llm.provider],
            })

        elif dim.name == "Syntax validity":
            adjustments.append({
                "action": "upgrade_model",
                "reason": "syntax errors in output",
            })

        elif dim.name == "Completeness":
            adjustments.append({
                "action": "upgrade_model",
                "reason": "incomplete output",
            })
            adjustments.append({
                "action": "re_search",
                "reason": "find MCP servers or skills for missing capabilities",
                "query_hints": [dim.details] if dim.details else [],
            })

    if not adjustments:
        adjustments.append({
            "action": "upgrade_model",
            "reason": "general improvement needed",
        })

    return adjustments


def apply_adjustments(
    stack: StackRecommendation,
    adjustments: list[dict],
) -> StackRecommendation:
    """Apply adjustments to the stack recommendation for retry."""
    new_stack = stack.model_copy(deep=True)
    new_stack.adjustment_notes = [f"{a['action']}: {a['reason']}" for a in adjustments]

    for adj in adjustments:
        action = adj["action"]

        if action == "upgrade_model":
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
                new_stack.llm.reason = f"Upgraded from previous attempt: {adj['reason']}"

    return new_stack


def get_re_search_hints(adjustments: list[dict]) -> list[str]:
    """Extract query hints from adjustments that need re-searching."""
    hints = []
    for adj in adjustments:
        if adj["action"] == "re_search":
            hints.extend(adj.get("query_hints", []))
    return hints
