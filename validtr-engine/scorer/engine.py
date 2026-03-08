"""Scoring Engine — routes to task-type-specific scorers."""

import logging

from models.result import ExecutionResult
from models.score import ScoreResult
from models.task import TaskDefinition, TaskType
from models.test_result import TestSuiteResult
from providers.base import LLMProvider
from scorer.code_scorer import CodeScorer

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Routes scoring to the appropriate task-type scorer."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.scorers = {
            TaskType.CODE_GENERATION: CodeScorer(provider),
        }

    async def score(
        self,
        task: TaskDefinition,
        execution: ExecutionResult,
        test_results: TestSuiteResult,
        threshold: float = 95.0,
    ) -> ScoreResult:
        """Score execution output based on task type."""
        scorer = self.scorers.get(task.type)
        if not scorer:
            logger.warning("No scorer for task type %s, using code scorer", task.type)
            scorer = self.scorers[TaskType.CODE_GENERATION]

        return await scorer.score(task, execution, test_results, threshold)
