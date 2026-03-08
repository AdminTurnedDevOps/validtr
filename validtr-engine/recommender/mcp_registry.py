"""MCP Registry lookup for discovering available MCP servers."""

import logging

import httpx

logger = logging.getLogger(__name__)

# Curated fallback registry of common MCP servers
CURATED_MCP_SERVERS = [
    {
        "name": "filesystem",
        "description": "Read and write files on the local filesystem",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-filesystem",
        "credentials": "none",
        "capabilities": ["file-read", "file-write", "directory-listing"],
    },
    {
        "name": "github",
        "description": "Interact with GitHub repositories, issues, PRs",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-github",
        "credentials": "GITHUB_TOKEN",
        "capabilities": ["repo-management", "issue-tracking", "pr-management"],
    },
    {
        "name": "postgres",
        "description": "Query and manage PostgreSQL databases",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-postgres",
        "credentials": "DATABASE_URL",
        "capabilities": ["sql-query", "schema-inspection", "data-management"],
    },
    {
        "name": "brave-search",
        "description": "Web search using Brave Search API",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-brave-search",
        "credentials": "BRAVE_API_KEY",
        "capabilities": ["web-search"],
    },
    {
        "name": "puppeteer",
        "description": "Browser automation with Puppeteer",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-puppeteer",
        "credentials": "none",
        "capabilities": ["web-scraping", "browser-automation", "screenshot"],
    },
    {
        "name": "memory",
        "description": "Persistent memory and knowledge graph",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-memory",
        "credentials": "none",
        "capabilities": ["knowledge-storage", "entity-relations"],
    },
    {
        "name": "fetch",
        "description": "Fetch and read web pages",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-fetch",
        "credentials": "none",
        "capabilities": ["web-fetch", "url-reading"],
    },
    {
        "name": "sequential-thinking",
        "description": "Step-by-step reasoning and problem decomposition",
        "transport": "stdio",
        "install": "npx -y @modelcontextprotocol/server-sequential-thinking",
        "credentials": "none",
        "capabilities": ["reasoning", "planning", "decomposition"],
    },
]


class MCPRegistryClient:
    """Queries MCP registries to discover available servers."""

    def __init__(self):
        self.curated = CURATED_MCP_SERVERS

    async def search(self, query: str, capabilities: list[str] | None = None) -> list[dict]:
        """Search for MCP servers matching the query and required capabilities."""
        # Try online registries first, fall back to curated list
        results = await self._search_online(query)
        if not results:
            results = self._search_curated(query, capabilities)
        return results

    async def _search_online(self, query: str) -> list[dict]:
        """Search mcp.so or Smithery for MCP servers."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try mcp.so search endpoint
                response = await client.get(
                    "https://registry.mcp.so/api/servers",
                    params={"q": query, "limit": 10},
                )
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "name": s.get("name", ""),
                            "description": s.get("description", ""),
                            "transport": s.get("transport", "stdio"),
                            "install": s.get("install_command", ""),
                            "credentials": s.get("credentials", "none"),
                            "capabilities": s.get("capabilities", []),
                            "source": "mcp.so",
                        }
                        for s in (data if isinstance(data, list) else data.get("servers", []))
                    ]
        except (httpx.HTTPError, Exception) as e:
            logger.debug("Online MCP registry search failed: %s", e)
        return []

    def _search_curated(
        self, query: str, capabilities: list[str] | None = None
    ) -> list[dict]:
        """Search the curated fallback registry."""
        query_lower = query.lower()
        results = []

        for server in self.curated:
            # Match on name, description, or capabilities
            name_match = query_lower in server["name"].lower()
            desc_match = query_lower in server["description"].lower()
            cap_match = any(query_lower in c for c in server["capabilities"])

            # Also check if any required capabilities match
            req_cap_match = False
            if capabilities:
                server_caps = set(server["capabilities"])
                req_cap_match = bool(server_caps & set(capabilities))

            if name_match or desc_match or cap_match or req_cap_match:
                results.append({**server, "source": "curated"})

        return results
