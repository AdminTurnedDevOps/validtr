"""Scorer for code generation tasks."""

import json
import logging

from models.result import ExecutionResult
from models.score import DimensionScore, ScoreResult
from models.task import TaskDefinition
from models.test_result import TestSuiteResult
from providers.base import LLMProvider, Message
from scorer.prompts import COMPLETENESS_JUDGE_SYSTEM, COMPLETENESS_JUDGE_USER

logger = logging.getLogger(__name__)

# Code task weights
TEST_PASSING_WEIGHT = 40
EXECUTION_WEIGHT = 25
SYNTAX_WEIGHT = 15
COMPLETENESS_WEIGHT = 20


class CodeScorer:
    """Scores code generation task output."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def score(
        self,
        task: TaskDefinition,
        execution: ExecutionResult,
        test_results: TestSuiteResult,
        threshold: float = 95.0,
    ) -> ScoreResult:
        """Compute composite score for a code generation task."""
        dimensions = []

        # 1. Test passing (40%)
        test_score = test_results.pass_rate * TEST_PASSING_WEIGHT
        dimensions.append(DimensionScore(
            name="Test passing",
            score=test_score,
            max_score=TEST_PASSING_WEIGHT,
            details=f"{test_results.passed}/{test_results.total} tests passed",
        ))

        # 2. Execution (25%) — did the task run without errors?
        exec_score = EXECUTION_WEIGHT if execution.success else 0
        dimensions.append(DimensionScore(
            name="Execution",
            score=exec_score,
            max_score=EXECUTION_WEIGHT,
            details="Execution succeeded" if execution.success else f"Failed: {execution.error}",
        ))

        # 3. Syntax validity (15%) — are the output files valid?
        syntax_score = self._check_syntax(execution.artifacts)
        dimensions.append(DimensionScore(
            name="Syntax validity",
            score=syntax_score,
            max_score=SYNTAX_WEIGHT,
            details="Syntax check on output files",
        ))

        # 4. Completeness (20%) — LLM-as-judge
        completeness_score = await self._judge_completeness(task, execution)
        dimensions.append(DimensionScore(
            name="Completeness",
            score=completeness_score,
            max_score=COMPLETENESS_WEIGHT,
            details="LLM judge assessment",
        ))

        composite = sum(d.score for d in dimensions)

        result = ScoreResult(
            composite_score=composite,
            dimensions=dimensions,
            threshold=threshold,
        )
        result.check_passed()

        logger.info("Score: %.1f/100 (%s)", composite, "PASS" if result.passed else "FAIL")
        return result

    def _check_syntax(self, artifacts: dict[str, str]) -> float:
        """Check syntax validity of Python files in artifacts."""
        if not artifacts:
            return 0.0

        python_files = {k: v for k, v in artifacts.items() if k.endswith(".py")}
        if not python_files:
            # No Python files — give full marks if there are other files
            return SYNTAX_WEIGHT if artifacts else 0.0

        valid = 0
        for name, content in python_files.items():
            try:
                compile(content, name, "exec")
                valid += 1
            except SyntaxError:
                logger.debug("Syntax error in %s", name)

        ratio = valid / len(python_files) if python_files else 0
        return ratio * SYNTAX_WEIGHT

    async def _judge_completeness(
        self,
        task: TaskDefinition,
        execution: ExecutionResult,
    ) -> float:
        """Use LLM-as-judge to assess completeness."""
        artifact_summary = ""
        for name, content in execution.artifacts.items():
            truncated = content[:1500] if len(content) > 1500 else content
            artifact_summary += f"\n--- {name} ---\n{truncated}\n"

        messages = [
            Message(role="system", content=COMPLETENESS_JUDGE_SYSTEM),
            Message(
                role="user",
                content=COMPLETENESS_JUDGE_USER.format(
                    task_description=task.raw_input,
                    success_criteria="\n".join(f"- {c}" for c in task.success_criteria),
                    artifact_summary=artifact_summary or "No artifacts",
                ),
            ),
        ]

        try:
            response = await self.provider.complete_json(messages=messages, max_tokens=512)
            data = json.loads(response.content)
            raw_score = max(0, min(100, data.get("score", 50)))
            return (raw_score / 100) * COMPLETENESS_WEIGHT
        except Exception as e:
            logger.warning("Completeness judge failed: %s, defaulting to 50%%", e)
            return COMPLETENESS_WEIGHT * 0.5
