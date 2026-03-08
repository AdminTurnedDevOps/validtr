"""Tests for all Pydantic models in the models package."""

import json

import pytest

from models.result import ExecutionResult, ExecutionTrace, LLMCall, ToolCall
from models.score import AttemptResult, DimensionScore, FinalResult, ScoreResult
from models.stack import (
    FrameworkRecommendation,
    LLMRecommendation,
    MCPServerRecommendation,
    MCPTransport,
    StackRecommendation,
)
from models.task import Complexity, TaskDefinition, TaskRequirements, TaskType
from models.test_result import SingleTestResult, TestStatus, TestSuiteResult


# ---------------------------------------------------------------------------
# TaskDefinition
# ---------------------------------------------------------------------------

class TestTaskDefinition:
    """Tests for TaskDefinition creation and serialization."""

    def test_create_minimal(self):
        td = TaskDefinition(
            id="task-1",
            raw_input="Build a REST API",
            type=TaskType.CODE_GENERATION,
            domain="web",
            requirements=TaskRequirements(),
            complexity=Complexity.SIMPLE,
        )
        assert td.id == "task-1"
        assert td.type == TaskType.CODE_GENERATION
        assert td.complexity == Complexity.SIMPLE
        assert td.success_criteria == []
        assert td.testable_assertions == []

    def test_create_full(self):
        td = TaskDefinition(
            id="task-2",
            raw_input="Deploy a K8s cluster",
            type=TaskType.INFRASTRUCTURE,
            domain="cloud",
            requirements=TaskRequirements(
                language="python",
                frameworks=["fastapi"],
                capabilities=["http", "auth"],
            ),
            complexity=Complexity.COMPLEX,
            success_criteria=["Cluster is reachable", "Nodes are ready"],
            testable_assertions=["kubectl get nodes returns 3 nodes"],
        )
        assert td.requirements.language == "python"
        assert len(td.requirements.frameworks) == 1
        assert len(td.success_criteria) == 2

    def test_serialization_roundtrip(self):
        td = TaskDefinition(
            id="task-3",
            raw_input="Research topic",
            type=TaskType.RESEARCH,
            domain="science",
            requirements=TaskRequirements(language="python"),
            complexity=Complexity.MODERATE,
            success_criteria=["Report generated"],
        )
        data = td.model_dump()
        assert data["type"] == "research"
        assert data["complexity"] == "moderate"

        restored = TaskDefinition.model_validate(data)
        assert restored == td

    def test_json_roundtrip(self):
        td = TaskDefinition(
            id="task-4",
            raw_input="Automate deployment",
            type=TaskType.AUTOMATION,
            domain="devops",
            requirements=TaskRequirements(),
            complexity=Complexity.SIMPLE,
        )
        json_str = td.model_dump_json()
        restored = TaskDefinition.model_validate_json(json_str)
        assert restored.id == td.id
        assert restored.type == TaskType.AUTOMATION

    def test_task_type_enum_values(self):
        assert TaskType.CODE_GENERATION == "code-generation"
        assert TaskType.INFRASTRUCTURE == "infrastructure"
        assert TaskType.RESEARCH == "research"
        assert TaskType.AUTOMATION == "automation"

    def test_complexity_enum_values(self):
        assert Complexity.SIMPLE == "simple"
        assert Complexity.MODERATE == "moderate"
        assert Complexity.COMPLEX == "complex"


# ---------------------------------------------------------------------------
# StackRecommendation
# ---------------------------------------------------------------------------

class TestStackRecommendation:
    """Tests for StackRecommendation and nested models."""

    def test_create_with_mcp_servers(self):
        stack = StackRecommendation(
            llm=LLMRecommendation(
                provider="anthropic",
                model="claude-sonnet-4-20250514",
                reason="Best for code",
            ),
            framework=FrameworkRecommendation(name="none"),
            mcp_servers=[
                MCPServerRecommendation(
                    name="filesystem",
                    transport=MCPTransport.STDIO,
                    install="npx -y @modelcontextprotocol/server-filesystem",
                    description="Read and write files",
                ),
                MCPServerRecommendation(
                    name="github",
                    transport=MCPTransport.STREAMABLE_HTTP,
                    install="npx -y @modelcontextprotocol/server-github",
                    credentials="GITHUB_TOKEN",
                    description="GitHub integration",
                ),
            ],
        )
        assert len(stack.mcp_servers) == 2
        assert stack.mcp_servers[0].transport == MCPTransport.STDIO
        assert stack.mcp_servers[1].credentials == "GITHUB_TOKEN"

    def test_defaults(self):
        stack = StackRecommendation(
            llm=LLMRecommendation(provider="openai", model="gpt-4o", reason="General"),
            framework=FrameworkRecommendation(),
        )
        assert stack.mcp_servers == []
        assert stack.skills == []
        assert stack.estimated_tokens == 0
        assert stack.estimated_cost == "$0.00"
        assert stack.adjustment_notes == []

    def test_mcp_transport_enum(self):
        assert MCPTransport.STDIO == "stdio"
        assert MCPTransport.STREAMABLE_HTTP == "streamable-http"

    def test_mcp_server_default_credentials(self):
        server = MCPServerRecommendation(
            name="test",
            transport=MCPTransport.STDIO,
            install="npx test",
        )
        assert server.credentials == "none"
        assert server.description == ""

    def test_serialization_roundtrip(self):
        stack = StackRecommendation(
            llm=LLMRecommendation(provider="gemini", model="gemini-2.5-flash", reason="Fast"),
            framework=FrameworkRecommendation(name="langgraph", reason="Agent workflows"),
            mcp_servers=[
                MCPServerRecommendation(
                    name="memory",
                    transport=MCPTransport.STDIO,
                    install="npx -y @modelcontextprotocol/server-memory",
                ),
            ],
            skills=["code-review"],
            estimated_tokens=5000,
            estimated_cost="$0.05",
        )
        json_str = stack.model_dump_json()
        restored = StackRecommendation.model_validate_json(json_str)
        assert restored.llm.provider == "gemini"
        assert len(restored.mcp_servers) == 1
        assert restored.skills == ["code-review"]


# ---------------------------------------------------------------------------
# ScoreResult
# ---------------------------------------------------------------------------

class TestScoreResult:
    """Tests for ScoreResult.check_passed()."""

    def test_check_passed_above_threshold(self):
        sr = ScoreResult(composite_score=97.0, threshold=95.0)
        assert sr.check_passed() is True
        assert sr.passed is True

    def test_check_passed_at_threshold(self):
        sr = ScoreResult(composite_score=95.0, threshold=95.0)
        assert sr.check_passed() is True
        assert sr.passed is True

    def test_check_passed_below_threshold(self):
        sr = ScoreResult(composite_score=80.0, threshold=95.0)
        assert sr.check_passed() is False
        assert sr.passed is False

    def test_check_passed_zero_score(self):
        sr = ScoreResult(composite_score=0.0, threshold=95.0)
        assert sr.check_passed() is False

    def test_check_passed_custom_threshold(self):
        sr = ScoreResult(composite_score=50.0, threshold=50.0)
        assert sr.check_passed() is True

    def test_dimensions_list(self):
        sr = ScoreResult(
            composite_score=85.0,
            dimensions=[
                DimensionScore(name="tests", score=35.0, max_score=40.0),
                DimensionScore(name="exec", score=25.0, max_score=25.0),
                DimensionScore(name="syntax", score=15.0, max_score=15.0),
                DimensionScore(name="completeness", score=10.0, max_score=20.0),
            ],
        )
        assert len(sr.dimensions) == 4
        assert sr.dimensions[0].name == "tests"


# ---------------------------------------------------------------------------
# TestSuiteResult
# ---------------------------------------------------------------------------

class TestTestSuiteResult:
    """Tests for TestSuiteResult.pass_rate property."""

    def test_pass_rate_all_passed(self):
        tsr = TestSuiteResult(total=10, passed=10, failed=0, errors=0, skipped=0)
        assert tsr.pass_rate == 1.0

    def test_pass_rate_all_failed(self):
        tsr = TestSuiteResult(total=5, passed=0, failed=5, errors=0, skipped=0)
        assert tsr.pass_rate == 0.0

    def test_pass_rate_mixed(self):
        tsr = TestSuiteResult(total=10, passed=7, failed=2, errors=1, skipped=0)
        assert tsr.pass_rate == pytest.approx(0.7)

    def test_pass_rate_with_skipped(self):
        tsr = TestSuiteResult(total=8, passed=5, failed=1, errors=0, skipped=2)
        assert tsr.pass_rate == pytest.approx(5 / 8)

    def test_pass_rate_zero_total(self):
        tsr = TestSuiteResult(total=0, passed=0, failed=0, errors=0, skipped=0)
        assert tsr.pass_rate == 0.0

    def test_pass_rate_one_test(self):
        tsr = TestSuiteResult(total=1, passed=1)
        assert tsr.pass_rate == 1.0

    def test_pass_rate_all_errors(self):
        tsr = TestSuiteResult(total=3, passed=0, failed=0, errors=3, skipped=0)
        assert tsr.pass_rate == 0.0

    def test_pass_rate_all_skipped(self):
        tsr = TestSuiteResult(total=4, passed=0, failed=0, errors=0, skipped=4)
        assert tsr.pass_rate == 0.0

    def test_with_test_objects(self):
        tests = [
            SingleTestResult(name="test_a", status=TestStatus.PASSED),
            SingleTestResult(name="test_b", status=TestStatus.FAILED, message="AssertionError"),
            SingleTestResult(name="test_c", status=TestStatus.SKIPPED),
            SingleTestResult(name="test_d", status=TestStatus.ERROR, message="ImportError"),
        ]
        tsr = TestSuiteResult(
            tests=tests,
            total=4,
            passed=1,
            failed=1,
            errors=1,
            skipped=1,
        )
        assert tsr.pass_rate == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# FinalResult
# ---------------------------------------------------------------------------

class TestFinalResult:
    """Tests for FinalResult with attempts list."""

    def test_create_with_attempts(self):
        attempts = [
            AttemptResult(
                attempt_number=1,
                score=ScoreResult(composite_score=70.0, threshold=95.0),
                artifacts={"main.py": "print('hello')"},
            ),
            AttemptResult(
                attempt_number=2,
                score=ScoreResult(composite_score=96.0, threshold=95.0),
                artifacts={"main.py": "print('hello world')"},
                adjustment_notes=["upgrade_model: 3 tests failed"],
            ),
        ]
        fr = FinalResult(
            run_id="run-abc",
            task_description="Build something",
            best_score=96.0,
            best_attempt=2,
            total_attempts=2,
            attempts=attempts,
            artifacts=attempts[1].artifacts,
            score=96.0,
            passed=True,
        )
        assert fr.total_attempts == 2
        assert fr.best_score == 96.0
        assert fr.best_attempt == 2
        assert fr.passed is True
        assert len(fr.attempts) == 2
        assert fr.attempts[1].adjustment_notes == ["upgrade_model: 3 tests failed"]

    def test_defaults(self):
        fr = FinalResult(run_id="run-1", task_description="Test")
        assert fr.best_score == 0.0
        assert fr.total_attempts == 0
        assert fr.attempts == []
        assert fr.artifacts == {}
        assert fr.passed is False
        assert fr.total_cost == "$0.00"
        assert fr.total_tokens == 0


# ---------------------------------------------------------------------------
# ExecutionResult
# ---------------------------------------------------------------------------

class TestExecutionResult:
    """Tests for ExecutionResult with and without artifacts."""

    def test_with_artifacts(self):
        er = ExecutionResult(
            run_id="run-123",
            artifacts={
                "main.py": "print('hello')",
                "utils.py": "def helper(): pass",
            },
            output_dir="/tmp/validtr/run-123/workspace/output",
            success=True,
        )
        assert len(er.artifacts) == 2
        assert "main.py" in er.artifacts
        assert er.success is True
        assert er.error is None

    def test_without_artifacts(self):
        er = ExecutionResult(run_id="run-456")
        assert er.artifacts == {}
        assert er.success is True
        assert er.error is None
        assert er.output_dir == ""

    def test_with_error(self):
        er = ExecutionResult(
            run_id="run-err",
            success=False,
            error="Container crashed",
        )
        assert er.success is False
        assert er.error == "Container crashed"

    def test_with_trace(self):
        trace = ExecutionTrace(
            llm_calls=[
                LLMCall(provider="anthropic", model="claude-sonnet-4-20250514", input_tokens=500, output_tokens=200),
            ],
            tool_calls=[
                ToolCall(tool_name="write_file", arguments={"path": "main.py"}, result="File written"),
            ],
            total_tokens=700,
            total_duration_ms=3000,
        )
        er = ExecutionResult(run_id="run-traced", trace=trace)
        assert len(er.trace.llm_calls) == 1
        assert len(er.trace.tool_calls) == 1
        assert er.trace.total_tokens == 700

    def test_serialization_roundtrip(self):
        er = ExecutionResult(
            run_id="run-rt",
            artifacts={"app.py": "import flask"},
            success=True,
        )
        json_str = er.model_dump_json()
        restored = ExecutionResult.model_validate_json(json_str)
        assert restored.run_id == "run-rt"
        assert restored.artifacts == {"app.py": "import flask"}
