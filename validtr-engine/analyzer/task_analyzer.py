"""Task Analyzer — classifies and structures a raw task description."""

import json
import logging
import uuid

from analyzer.prompts import TASK_ANALYSIS_SYSTEM, TASK_ANALYSIS_USER
from models.task import Complexity, TaskDefinition, TaskRequirements, TaskType
from providers.base import LLMProvider, Message

logger = logging.getLogger(__name__)


class TaskAnalyzer:
    """Analyzes a raw task description and produces a structured TaskDefinition."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def analyze(self, task_description: str) -> TaskDefinition:
        """Analyze a task description and return a structured TaskDefinition."""
        logger.info("Analyzing task: %s", task_description[:80])

        messages = [
            Message(role="system", content=TASK_ANALYSIS_SYSTEM),
            Message(role="user", content=TASK_ANALYSIS_USER.format(task_description=task_description)),
        ]

        response = await self.provider.complete_json(messages=messages, max_tokens=2048)

        raw = response.content.strip()
        # Strip markdown code fences if present (```json ... ```)
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = lines[1:]  # drop opening ```json
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse task analysis JSON: %s", e)
            raise ValueError(f"LLM returned invalid JSON for task analysis: {e}") from e

        task_id = uuid.uuid4().hex[:6]

        return TaskDefinition(
            id=task_id,
            raw_input=task_description,
            type=TaskType(data["type"]),
            domain=data.get("domain", "general"),
            requirements=TaskRequirements(
                language=data.get("requirements", {}).get("language"),
                frameworks=data.get("requirements", {}).get("frameworks", []),
                capabilities=data.get("requirements", {}).get("capabilities", []),
            ),
            complexity=Complexity(data.get("complexity", "moderate")),
            success_criteria=data.get("success_criteria", []),
            testable_assertions=data.get("testable_assertions", []),
        )
