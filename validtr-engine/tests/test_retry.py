"""Tests for RetryController, analyze_failures, and apply_adjustments."""

import pytest

from models.score import DimensionScore, ScoreResult
from models.stack import (
    FrameworkRecommendation,
    LLMRecommendation,
    MCPServerRecommendation,
    MCPTransport,
    StackRecommendation,
)
from models.test_result import SingleTestResult, TestStatus, TestSuiteResult
from retry.analysis import MODEL_UPGRADES, analyze_failures, apply_adjustments
from retry.controller import RetryController


def _make_score(composite: float, threshold: float = 95.0) -> ScoreResult:
    return ScoreResult(composite_score=composite, threshold=threshold)


def _make_stack(
    provider: str = "anthropic",
    model: str = "claude-sonnet-4-20250514",
) -> StackRecommendation:
    return StackRecommendation(
        llm=LLMRecommendation(provider=provider, model=model, reason="test"),
        framework=FrameworkRecommendation(),
    )


# ---------------------------------------------------------------------------
# RetryController.should_retry
# ---------------------------------------------------------------------------

class TestShouldRetry:
    """Tests for RetryController.should_retry()."""

    def test_returns_false_when_score_meets_threshold(self):
        rc = RetryController(max_retries=3, threshold=95.0)
        score = _make_score(96.0, 95.0)
        assert rc.should_retry(score, attempt_number=1) is False

    def test_returns_false_when_score_equals_threshold(self):
        rc = RetryController(max_retries=3, threshold=95.0)
        score = _make_score(95.0, 95.0)
        assert rc.should_retry(score, attempt_number=1) is False

    def test_returns_false_when_max_retries_reached(self):
        rc = RetryController(max_retries=3, threshold=95.0)
        score = _make_score(50.0, 95.0)
        assert rc.should_retry(score, attempt_number=3) is False

    def test_returns_false_when_max_retries_exceeded(self):
        rc = RetryController(max_retries=2, threshold=95.0)
        score = _make_score(50.0, 95.0)
        assert rc.should_retry(score, attempt_number=5) is False

    def test_returns_true_when_score_below_and_retries_remain(self):
        rc = RetryController(max_retries=3, threshold=95.0)
        score = _make_score(70.0, 95.0)
        assert rc.should_retry(score, attempt_number=1) is True

    def test_returns_true_on_second_attempt(self):
        rc = RetryController(max_retries=3, threshold=95.0)
        score = _make_score(80.0, 95.0)
        assert rc.should_retry(score, attempt_number=2) is True

    def test_returns_true_just_below_threshold(self):
        rc = RetryController(max_retries=3, threshold=95.0)
        score = _make_score(94.9, 95.0)
        assert rc.should_retry(score, attempt_number=1) is True

    def test_custom_threshold(self):
        rc = RetryController(max_retries=5, threshold=80.0)
        score = _make_score(79.0, 80.0)
        assert rc.should_retry(score, attempt_number=1) is True

        score_pass = _make_score(80.0, 80.0)
        assert rc.should_retry(score_pass, attempt_number=1) is False


# ---------------------------------------------------------------------------
# RetryController.record_attempt / get_best_attempt
# ---------------------------------------------------------------------------

class TestRecordAndBestAttempt:
    """Tests for record_attempt() and get_best_attempt()."""

    def test_get_best_attempt_empty(self):
        rc = RetryController()
        assert rc.get_best_attempt() is None

    def test_single_attempt(self):
        rc = RetryController()
        rc.record_attempt(1, _make_score(75.0), {"main.py": "code"})
        best = rc.get_best_attempt()
        assert best is not None
        assert best.attempt_number == 1
        assert best.score.composite_score == 75.0

    def test_best_attempt_returns_highest_score(self):
        rc = RetryController()
        rc.record_attempt(1, _make_score(70.0), {"main.py": "v1"})
        rc.record_attempt(2, _make_score(90.0), {"main.py": "v2"})
        rc.record_attempt(3, _make_score(85.0), {"main.py": "v3"})

        best = rc.get_best_attempt()
        assert best is not None
        assert best.attempt_number == 2
        assert best.score.composite_score == 90.0

    def test_record_attempt_stores_artifacts(self):
        rc = RetryController()
        rc.record_attempt(
            1,
            _make_score(80.0),
            {"main.py": "print('hello')"},
            test_code="def test_main(): pass",
            adjustment_notes=["upgrade_model: 2 tests failed"],
        )
        assert len(rc.attempts) == 1
        assert rc.attempts[0].artifacts == {"main.py": "print('hello')"}
        assert rc.attempts[0].test_code == "def test_main(): pass"
        assert rc.attempts[0].adjustment_notes == ["upgrade_model: 2 tests failed"]

    def test_multiple_equal_scores(self):
        rc = RetryController()
        rc.record_attempt(1, _make_score(80.0), {})
        rc.record_attempt(2, _make_score(80.0), {})
        best = rc.get_best_attempt()
        # max() returns the first element on ties
        assert best is not None
        assert best.score.composite_score == 80.0


# ---------------------------------------------------------------------------
# analyze_failures
# ---------------------------------------------------------------------------

class TestAnalyzeFailures:
    """Tests for analyze_failures()."""

    def test_failed_tests_suggest_upgrade(self):
        score = ScoreResult(
            composite_score=60.0,
            dimensions=[
                DimensionScore(name="Test passing", score=20.0, max_score=40.0),
                DimensionScore(name="Execution", score=25.0, max_score=25.0),
                DimensionScore(name="Syntax validity", score=15.0, max_score=15.0),
                DimensionScore(name="Completeness", score=0.0, max_score=20.0),
            ],
        )
        test_results = TestSuiteResult(
            tests=[
                SingleTestResult(name="test_a", status=TestStatus.PASSED),
                SingleTestResult(name="test_b", status=TestStatus.FAILED),
                SingleTestResult(name="test_c", status=TestStatus.FAILED),
            ],
            total=3,
            passed=1,
            failed=2,
        )
        stack = _make_stack()
        adjustments = analyze_failures(score, test_results, stack)
        assert any("upgrade_model" in a for a in adjustments)

    def test_execution_failure_suggests_check_deps(self):
        score = ScoreResult(
            composite_score=55.0,
            dimensions=[
                DimensionScore(name="Test passing", score=40.0, max_score=40.0),
                DimensionScore(name="Execution", score=0.0, max_score=25.0),
                DimensionScore(name="Syntax validity", score=15.0, max_score=15.0),
                DimensionScore(name="Completeness", score=0.0, max_score=20.0),
            ],
        )
        test_results = TestSuiteResult(total=5, passed=5)
        stack = _make_stack()
        adjustments = analyze_failures(score, test_results, stack)
        assert any("check_dependencies" in a for a in adjustments)

    def test_syntax_failure_suggests_upgrade(self):
        score = ScoreResult(
            composite_score=50.0,
            dimensions=[
                DimensionScore(name="Test passing", score=40.0, max_score=40.0),
                DimensionScore(name="Execution", score=25.0, max_score=25.0),
                DimensionScore(name="Syntax validity", score=0.0, max_score=15.0),
                DimensionScore(name="Completeness", score=0.0, max_score=20.0),
            ],
        )
        test_results = TestSuiteResult(total=5, passed=5)
        stack = _make_stack()
        adjustments = analyze_failures(score, test_results, stack)
        assert any("syntax" in a for a in adjustments)

    def test_completeness_failure_suggests_mcp(self):
        score = ScoreResult(
            composite_score=80.0,
            dimensions=[
                DimensionScore(name="Test passing", score=40.0, max_score=40.0),
                DimensionScore(name="Execution", score=25.0, max_score=25.0),
                DimensionScore(name="Syntax validity", score=15.0, max_score=15.0),
                DimensionScore(name="Completeness", score=0.0, max_score=20.0),
            ],
        )
        test_results = TestSuiteResult(total=5, passed=5)
        stack = _make_stack()
        adjustments = analyze_failures(score, test_results, stack)
        assert any("add_mcp_server" in a for a in adjustments)

    def test_all_high_scores_fallback(self):
        score = ScoreResult(
            composite_score=94.0,
            dimensions=[
                DimensionScore(name="Test passing", score=39.0, max_score=40.0),
                DimensionScore(name="Execution", score=25.0, max_score=25.0),
                DimensionScore(name="Syntax validity", score=15.0, max_score=15.0),
                DimensionScore(name="Completeness", score=15.0, max_score=20.0),
            ],
        )
        test_results = TestSuiteResult(total=5, passed=5)
        stack = _make_stack()
        adjustments = analyze_failures(score, test_results, stack)
        # Should still produce adjustments even if individual ratios are high
        assert len(adjustments) > 0

    def test_returns_non_empty_list(self):
        score = ScoreResult(
            composite_score=50.0,
            dimensions=[
                DimensionScore(name="Test passing", score=20.0, max_score=40.0),
            ],
        )
        test_results = TestSuiteResult(
            tests=[SingleTestResult(name="t", status=TestStatus.FAILED)],
            total=1,
            failed=1,
        )
        stack = _make_stack()
        adjustments = analyze_failures(score, test_results, stack)
        assert isinstance(adjustments, list)
        assert len(adjustments) > 0


# ---------------------------------------------------------------------------
# apply_adjustments
# ---------------------------------------------------------------------------

class TestApplyAdjustments:
    """Tests for apply_adjustments()."""

    def test_upgrade_model_anthropic(self):
        stack = _make_stack(provider="anthropic", model="claude-sonnet-4-20250514")
        adjustments = ["upgrade_model: tests failed"]
        new_stack = apply_adjustments(stack, adjustments)
        assert new_stack.llm.model == "claude-opus-4-20250514"
        assert new_stack.adjustment_notes == adjustments

    def test_upgrade_model_openai(self):
        stack = _make_stack(provider="openai", model="gpt-4o-mini")
        adjustments = ["upgrade_model: tests failed"]
        new_stack = apply_adjustments(stack, adjustments)
        assert new_stack.llm.model == "gpt-4o"

    def test_upgrade_model_already_best(self):
        stack = _make_stack(provider="anthropic", model="claude-opus-4-20250514")
        adjustments = ["upgrade_model: tests failed"]
        new_stack = apply_adjustments(stack, adjustments)
        # Already at the best model, should stay the same
        assert new_stack.llm.model == "claude-opus-4-20250514"

    def test_no_upgrade_for_check_dependencies(self):
        stack = _make_stack(provider="openai", model="gpt-4o")
        adjustments = ["check_dependencies: execution failure"]
        new_stack = apply_adjustments(stack, adjustments)
        # check_dependencies doesn't trigger model upgrade
        assert new_stack.llm.model == "gpt-4o"
        assert new_stack.adjustment_notes == adjustments

    def test_original_stack_unchanged(self):
        stack = _make_stack(provider="openai", model="gpt-4o-mini")
        adjustments = ["upgrade_model: tests failed"]
        new_stack = apply_adjustments(stack, adjustments)
        # Original stack should not be mutated
        assert stack.llm.model == "gpt-4o-mini"
        assert new_stack.llm.model == "gpt-4o"

    def test_adjustment_notes_set(self):
        stack = _make_stack()
        adjustments = ["upgrade_model: a", "add_mcp_server: b"]
        new_stack = apply_adjustments(stack, adjustments)
        assert new_stack.adjustment_notes == adjustments

    def test_model_upgrades_map_structure(self):
        assert "anthropic" in MODEL_UPGRADES
        assert "openai" in MODEL_UPGRADES
        assert "gemini" in MODEL_UPGRADES
        for provider, models in MODEL_UPGRADES.items():
            assert isinstance(models, list)
            assert len(models) >= 2, f"{provider} should have at least 2 models in upgrade path"
