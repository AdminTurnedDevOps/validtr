"""Web search integration for the Recommendation Engine."""

import logging

import httpx

logger = logging.getLogger(__name__)


class WebSearchProvider:
    """Pluggable web search. Supports Tavily (default) or returns empty results."""

    def __init__(self, api_key: str | None = None, provider: str = "tavily"):
        self.api_key = api_key
        self.provider = provider

    async def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Search the web for relevant information."""
        if not self.api_key:
            logger.warning("No search API key configured, skipping web search")
            return []

        if self.provider == "tavily":
            return await self._tavily_search(query, max_results)

        logger.warning("Unknown search provider: %s", self.provider)
        return []

    async def _tavily_search(self, query: str, max_results: int) -> list[dict]:
        """Search using Tavily API."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.api_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "basic",
                    },
                )
                response.raise_for_status()
                data = response.json()
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", ""),
                    }
                    for r in data.get("results", [])
                ]
        except httpx.HTTPError as e:
            logger.error("Web search failed: %s", e)
            return []
