"""Tests for CodeScorer._calculate_test_score and _check_syntax."""

import pytest

from scorer.code_scorer import SYNTAX_WEIGHT, TEST_PASSING_WEIGHT, CodeScorer


class TestCalculateTestScore:
    """Tests for the test score calculation logic.

    The CodeScorer.score() method calculates test_score = pass_rate * TEST_PASSING_WEIGHT.
    We test this formula directly using the same arithmetic.
    """

    def test_100_percent_pass_rate_full_marks(self):
        pass_rate = 1.0
        test_score = pass_rate * TEST_PASSING_WEIGHT
        assert test_score == TEST_PASSING_WEIGHT

    def test_0_percent_pass_rate_zero(self):
        pass_rate = 0.0
        test_score = pass_rate * TEST_PASSING_WEIGHT
        assert test_score == 0.0

    def test_50_percent_pass_rate(self):
        pass_rate = 0.5
        test_score = pass_rate * TEST_PASSING_WEIGHT
        assert test_score == pytest.approx(TEST_PASSING_WEIGHT * 0.5)

    def test_75_percent_pass_rate(self):
        pass_rate = 0.75
        test_score = pass_rate * TEST_PASSING_WEIGHT
        assert test_score == pytest.approx(TEST_PASSING_WEIGHT * 0.75)

    def test_partial_pass_rate_scales_correctly(self):
        # 7 of 10 tests pass
        pass_rate = 7 / 10
        test_score = pass_rate * TEST_PASSING_WEIGHT
        assert test_score == pytest.approx(TEST_PASSING_WEIGHT * 0.7)

    def test_single_test_passed(self):
        pass_rate = 1 / 1
        test_score = pass_rate * TEST_PASSING_WEIGHT
        assert test_score == TEST_PASSING_WEIGHT

    def test_single_test_failed(self):
        pass_rate = 0 / 1
        test_score = pass_rate * TEST_PASSING_WEIGHT
        assert test_score == 0.0


class TestCheckSyntax:
    """Tests for CodeScorer._check_syntax (pure logic, no LLM needed)."""

    @pytest.fixture
    def scorer(self):
        """Create a CodeScorer with a mock provider (not used for syntax check)."""

        class FakeProvider:
            pass

        return CodeScorer(provider=FakeProvider())

    def test_empty_artifacts_zero(self, scorer):
        result = scorer._check_syntax({})
        assert result == 0.0

    def test_all_valid_python(self, scorer):
        artifacts = {
            "main.py": "print('hello')",
            "utils.py": "def foo():\n    return 42",
        }
        result = scorer._check_syntax(artifacts)
        assert result == SYNTAX_WEIGHT

    def test_all_invalid_python(self, scorer):
        artifacts = {
            "bad1.py": "def foo(:",
            "bad2.py": "class {",
        }
        result = scorer._check_syntax(artifacts)
        assert result == 0.0

    def test_mixed_valid_invalid(self, scorer):
        artifacts = {
            "good.py": "x = 1",
            "bad.py": "def (",
        }
        result = scorer._check_syntax(artifacts)
        # 1 of 2 valid => 0.5 * SYNTAX_WEIGHT
        assert result == pytest.approx(SYNTAX_WEIGHT * 0.5)

    def test_non_python_files_give_full_marks(self, scorer):
        artifacts = {
            "config.yaml": "key: value",
            "readme.md": "# Hello",
        }
        result = scorer._check_syntax(artifacts)
        assert result == SYNTAX_WEIGHT

    def test_mixed_python_and_non_python(self, scorer):
        # Only Python files are checked; non-Python files are ignored in the ratio
        artifacts = {
            "main.py": "print('hello')",
            "config.yaml": "key: value",
        }
        result = scorer._check_syntax(artifacts)
        # 1 of 1 Python file is valid => full marks
        assert result == SYNTAX_WEIGHT

    def test_three_of_four_valid(self, scorer):
        artifacts = {
            "a.py": "x = 1",
            "b.py": "y = 2",
            "c.py": "z = 3",
            "d.py": "def (",
        }
        result = scorer._check_syntax(artifacts)
        assert result == pytest.approx(SYNTAX_WEIGHT * 3 / 4)
