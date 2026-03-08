"""Tests for TestGenerator._parse_pytest_output."""

import pytest

from models.test_result import TestStatus
from test_generator.engine import TestGenerator


class TestParsePytestOutput:
    """Tests for _parse_pytest_output method."""

    @pytest.fixture
    def generator(self):
        """Create a TestGenerator with a fake provider (not used for parsing)."""

        class FakeProvider:
            pass

        return TestGenerator(provider=FakeProvider())

    def test_parse_mixed_results(self, generator):
        output = """
tests/test_example.py::test_add PASSED
tests/test_example.py::test_subtract FAILED
tests/test_example.py::test_multiply PASSED
tests/test_example.py::test_divide ERROR
tests/test_example.py::test_modulo SKIPPED
"""
        result = generator._parse_pytest_output(output)
        assert result.total == 5
        assert result.passed == 2
        assert result.failed == 1
        assert result.errors == 1
        assert result.skipped == 1
        assert result.pass_rate == pytest.approx(2 / 5)

    def test_parse_all_passed(self, generator):
        output = """
test_a PASSED
test_b PASSED
test_c PASSED
"""
        result = generator._parse_pytest_output(output)
        assert result.total == 3
        assert result.passed == 3
        assert result.failed == 0
        assert result.pass_rate == 1.0

    def test_parse_all_failed(self, generator):
        output = """
test_x FAILED
test_y FAILED
"""
        result = generator._parse_pytest_output(output)
        assert result.total == 2
        assert result.passed == 0
        assert result.failed == 2
        assert result.pass_rate == 0.0

    def test_parse_empty_output(self, generator):
        result = generator._parse_pytest_output("")
        assert result.total == 0
        assert result.passed == 0
        assert result.failed == 0
        assert result.errors == 0
        assert result.skipped == 0
        assert result.pass_rate == 0.0
        assert result.tests == []

    def test_parse_no_matching_lines(self, generator):
        output = """
============================= test session starts =============================
platform linux -- Python 3.12.0
collected 0 items

============================= no tests ran =============================
"""
        result = generator._parse_pytest_output(output)
        assert result.total == 0
        assert result.pass_rate == 0.0

    def test_parse_preserves_test_names(self, generator):
        output = """
tests/test_models.py::TestTask::test_create PASSED
tests/test_models.py::TestTask::test_validate FAILED
"""
        result = generator._parse_pytest_output(output)
        assert result.total == 2
        names = [t.name for t in result.tests]
        assert "tests/test_models.py::TestTask::test_create" in names
        assert "tests/test_models.py::TestTask::test_validate" in names

    def test_parse_statuses_correct(self, generator):
        output = """
test_one PASSED
test_two FAILED
test_three ERROR
test_four SKIPPED
"""
        result = generator._parse_pytest_output(output)
        status_map = {t.name: t.status for t in result.tests}
        assert status_map["test_one"] == TestStatus.PASSED
        assert status_map["test_two"] == TestStatus.FAILED
        assert status_map["test_three"] == TestStatus.ERROR
        assert status_map["test_four"] == TestStatus.SKIPPED

    def test_runner_output_preserved(self, generator):
        output = "test_a PASSED\ntest_b FAILED\n"
        result = generator._parse_pytest_output(output)
        assert result.runner_output == output

    def test_pass_rate_calculation(self, generator):
        output = """
test_1 PASSED
test_2 PASSED
test_3 PASSED
test_4 FAILED
test_5 SKIPPED
"""
        result = generator._parse_pytest_output(output)
        assert result.total == 5
        assert result.pass_rate == pytest.approx(3 / 5)
