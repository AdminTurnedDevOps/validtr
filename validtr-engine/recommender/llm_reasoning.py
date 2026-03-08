"""LLM reasoning component of the Recommendation Engine."""

import json
import logging

from models.stack import (
    FrameworkRecommendation,
    LLMRecommendation,
    MCPServerRecommendation,
    MCPTransport,
    StackRecommendation,
)
from models.task import TaskDefinition
from providers.base import LLMProvider, Message
from recommender.prompts import RECOMMENDATION_SYSTEM, RECOMMENDATION_USER

logger = logging.getLogger(__name__)


class LLMReasoningEngine:
    """Uses an LLM to synthesize search results and registry data into a stack recommendation."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    async def recommend(
        self,
        task: TaskDefinition,
        web_results: list[dict],
        mcp_servers: list[dict],
        preferred_provider: str | None = None,
    ) -> StackRecommendation:
        """Generate a stack recommendation using LLM reasoning."""
        messages = [
            Message(role="system", content=RECOMMENDATION_SYSTEM),
            Message(
                role="user",
                content=RECOMMENDATION_USER.format(
                    task_definition=task.model_dump_json(indent=2),
                    web_results=json.dumps(web_results, indent=2) if web_results else "No results",
                    mcp_servers=json.dumps(mcp_servers, indent=2) if mcp_servers else "No results",
                    preferred_provider=preferred_provider or "none (choose the best)",
                ),
            ),
        ]

        response = await self.provider.complete_json(messages=messages, max_tokens=2048)

        raw = response.content.strip()
        # Strip markdown code fences that some models wrap JSON in
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = lines[1:]  # drop ```json or ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse recommendation JSON: %s\nRaw: %s", e, raw[:500])
            raise ValueError(f"LLM returned invalid JSON for recommendation: {e}") from e

        llm_data = data["llm"]
        framework_data = data.get("framework", {})
        mcp_list = data.get("mcp_servers", [])

        return StackRecommendation(
            llm=LLMRecommendation(
                provider=llm_data["provider"],
                model=llm_data["model"],
                reason=llm_data.get("reason", ""),
            ),
            framework=FrameworkRecommendation(
                name=framework_data.get("name"),
                reason=framework_data.get("reason", ""),
            ),
            mcp_servers=[
                MCPServerRecommendation(
                    name=s["name"],
                    transport=MCPTransport(s.get("transport", "stdio")),
                    install=s.get("install", ""),
                    credentials=s.get("credentials", "none"),
                    description=s.get("description", ""),
                )
                for s in mcp_list
            ],
            skills=data.get("skills", ["code-generation", "test-generation"]),
            prompt_strategy=data.get(
                "prompt_strategy",
                "Decompose requirements, implement incrementally, validate with tests, then refine.",
            ),
            estimated_tokens=data.get("estimated_tokens", 15000),
            estimated_cost=data.get("estimated_cost", "$0.04"),
        )
