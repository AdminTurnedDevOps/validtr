"""Prompts for the Scoring Engine (LLM-as-judge for completeness)."""

COMPLETENESS_JUDGE_SYSTEM = """You are a code quality judge. Given a task description, success criteria, and the output artifacts, score the COMPLETENESS of the output on a scale of 0-100.

Score based on:
- Does the output address all parts of the task description?
- Are all success criteria met?
- Is the output production-quality or just a skeleton?
- Are edge cases handled?

Respond with JSON only:
{
  "score": integer (0-100),
  "reasoning": string (1-2 sentences explaining the score)
}"""

COMPLETENESS_JUDGE_USER = """Task: {task_description}

Success Criteria:
{success_criteria}

Output Artifacts:
{artifact_summary}

Score the completeness of this output (0-100)."""
