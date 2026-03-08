"""Recommendation Engine — orchestrates web search, MCP registry, and LLM reasoning."""

import asyncio
import logging

from models.stack import StackRecommendation
from models.task import TaskDefinition
from providers.base import LLMProvider
from recommender.llm_reasoning import LLMReasoningEngine
from recommender.mcp_registry import MCPRegistryClient
from recommender.web_search import WebSearchProvider

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Combines web search, MCP registry lookup, and LLM reasoning to recommend a stack."""

    def __init__(
        self,
        provider: LLMProvider,
        search_api_key: str | None = None,
        search_provider: str = "tavily",
    ):
        self.web_search = WebSearchProvider(api_key=search_api_key, provider=search_provider)
        self.mcp_registry = MCPRegistryClient()
        self.llm_reasoning = LLMReasoningEngine(provider=provider)

    async def recommend(
        self,
        task: TaskDefinition,
        preferred_provider: str | None = None,
    ) -> StackRecommendation:
        """Generate a stack recommendation for the given task."""
        logger.info("Generating recommendation for task: %s", task.id)

        # Build search queries from task
        search_query = f"best {task.type.value} tools for {task.domain} {' '.join(task.requirements.frameworks)}"
        mcp_query = " ".join(task.requirements.capabilities[:3]) if task.requirements.capabilities else task.domain

        # Run web search and MCP registry lookup in parallel
        web_results, mcp_servers = await asyncio.gather(
            self.web_search.search(search_query),
            self.mcp_registry.search(mcp_query, task.requirements.capabilities),
        )

        logger.info("Web search: %d results, MCP registry: %d servers", len(web_results), len(mcp_servers))

        # Use LLM to synthesize into a recommendation
        recommendation = await self.llm_reasoning.recommend(
            task=task,
            web_results=web_results,
            mcp_servers=mcp_servers,
            preferred_provider=preferred_provider,
        )

        logger.info(
            "Recommended: %s/%s, %d MCP servers",
            recommendation.llm.provider,
            recommendation.llm.model,
            len(recommendation.mcp_servers),
        )

        return recommendation

    async def search_additional(
        self,
        task: TaskDefinition,
        query_hints: list[str],
    ) -> list:
        """Run additional MCP registry + web searches based on failure hints.

        Returns a list of MCPServerRecommendation objects found.
        """
        from models.stack import MCPServerRecommendation, MCPTransport

        all_servers = []
        seen_names: set[str] = set()

        for hint in query_hints[:3]:  # limit to 3 queries
            mcp_results = await self.mcp_registry.search(hint)
            for s in mcp_results:
                name = s.get("name", "")
                if name and name not in seen_names:
                    seen_names.add(name)
                    all_servers.append(
                        MCPServerRecommendation(
                            name=name,
                            transport=MCPTransport(s.get("transport", "stdio")),
                            install=s.get("install", ""),
                            credentials=s.get("credentials", "none"),
                            description=s.get("description", ""),
                        )
                    )

        return all_servers
