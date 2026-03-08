"""MCP Registry — fetches MCP servers from upstream registries at runtime.

Sources (in priority order):
  1. Official MCP Registry: https://registry.modelcontextprotocol.io
  2. Smithery: https://registry.smithery.ai

Servers are fetched on first use, cached for 1 hour. No local curation needed.
"""

import logging
import time

import httpx

logger = logging.getLogger(__name__)

# Cache TTL in seconds (1 hour)
_CACHE_TTL = 3600

# Official MCP Registry API
_OFFICIAL_REGISTRY = "https://registry.modelcontextprotocol.io/v0.1/servers"

# Smithery API
_SMITHERY_API = "https://registry.smithery.ai/servers"


class MCPRegistryClient:
    """Fetches and caches MCP servers from upstream registries."""

    def __init__(self):
        self._cache: list[dict] | None = None
        self._cache_time: float = 0

    async def get_all(self) -> list[dict]:
        """Return all servers from upstream registries (cached)."""
        now = time.time()
        if self._cache is not None and (now - self._cache_time) < _CACHE_TTL:
            return self._cache

        servers = await self._fetch_official_registry()
        if not servers:
            logger.info("Official registry unavailable, trying Smithery")
            servers = await self._fetch_smithery_all()

        if servers:
            self._cache = servers
            self._cache_time = now
            logger.info("MCP registry: %d servers cached", len(servers))
        else:
            logger.warning("No MCP servers fetched from any registry")
            self._cache = []
            self._cache_time = now

        return self._cache

    async def get_relevant(self, query: str, limit: int = 50) -> list[dict]:
        """Get servers relevant to a query by filtering the cached registry."""
        all_servers = await self.get_all()
        if not query.strip():
            return all_servers[:limit]

        query_words = set(query.lower().split())
        scored = []

        for server in all_servers:
            score = 0
            name_lower = server["name"].lower()
            desc_lower = server["description"].lower()

            # Name match (strongest signal)
            if any(w in name_lower for w in query_words):
                score += 5
            # Description word match
            for w in query_words:
                if len(w) >= 3 and w in desc_lower:
                    score += 2

            if score > 0:
                scored.append((score, server))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:limit]]

    async def search(self, query: str, capabilities: list[str] | None = None) -> list[dict]:
        """Search upstream registries for servers matching the query."""
        # Try official registry search first
        results = await self._search_official(query)
        if results:
            return results

        # Fall back to Smithery search
        results = await self._search_smithery(query)
        if results:
            return results

        # Fall back to filtering cached data
        return await self.get_relevant(query, limit=10)

    # --- Official MCP Registry ---

    async def _fetch_official_registry(self) -> list[dict]:
        """Fetch all servers from the official MCP registry (paginated)."""
        all_servers = []
        cursor = None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                while True:
                    params: dict = {"version": "latest", "limit": 100}
                    if cursor:
                        params["cursor"] = cursor

                    resp = await client.get(_OFFICIAL_REGISTRY, params=params)
                    if resp.status_code != 200:
                        logger.warning(
                            "Official MCP registry returned %d", resp.status_code
                        )
                        break

                    data = resp.json()
                    page_servers = data.get("servers", [])
                    if not page_servers:
                        break

                    for entry in page_servers:
                        parsed = _parse_official_server(entry)
                        if parsed:
                            all_servers.append(parsed)

                    cursor = data.get("metadata", {}).get("nextCursor")
                    if not cursor:
                        break

        except (httpx.HTTPError, Exception) as e:
            logger.warning("Failed to fetch from official MCP registry: %s", e)

        return all_servers

    async def _search_official(self, query: str) -> list[dict]:
        """Search the official MCP registry."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    _OFFICIAL_REGISTRY,
                    params={"version": "latest", "search": query, "limit": 20},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for entry in data.get("servers", []):
                        parsed = _parse_official_server(entry)
                        if parsed:
                            results.append(parsed)
                    return results
        except (httpx.HTTPError, Exception) as e:
            logger.debug("Official registry search failed: %s", e)
        return []

    # --- Smithery ---

    async def _fetch_smithery_all(self) -> list[dict]:
        """Fetch servers from Smithery (first pages, sorted by popularity)."""
        all_servers = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch first 5 pages (500 most popular servers)
                for page in range(1, 6):
                    resp = await client.get(
                        _SMITHERY_API,
                        params={"pageSize": 100, "page": page},
                    )
                    if resp.status_code != 200:
                        break

                    data = resp.json()
                    page_servers = data.get("servers", [])
                    if not page_servers:
                        break

                    for s in page_servers:
                        parsed = _parse_smithery_server(s)
                        if parsed:
                            all_servers.append(parsed)

        except (httpx.HTTPError, Exception) as e:
            logger.warning("Failed to fetch from Smithery: %s", e)

        return all_servers

    async def _search_smithery(self, query: str) -> list[dict]:
        """Search Smithery for MCP servers."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    _SMITHERY_API,
                    params={"q": query, "pageSize": 20},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    for s in data.get("servers", []):
                        parsed = _parse_smithery_server(s)
                        if parsed:
                            results.append(parsed)
                    return results
        except (httpx.HTTPError, Exception) as e:
            logger.debug("Smithery search failed: %s", e)
        return []


def _parse_official_server(entry: dict) -> dict | None:
    """Parse a server entry from the official MCP registry API."""
    server = entry.get("server", {})
    name = server.get("name", "")
    description = server.get("description", "")
    if not name or not description:
        return None

    # Extract transport, install command, and credentials from packages
    transport = "stdio"
    install = ""
    credentials = "none"

    packages = server.get("packages", [])
    if packages:
        pkg = packages[0]
        transport = pkg.get("transport", {}).get("type", "stdio")
        identifier = pkg.get("identifier", "")
        runtime = pkg.get("runtimeHint", "")

        if runtime and identifier:
            install = f"{runtime} {identifier}"
        elif identifier:
            install = f"npx -y {identifier}"

        env_vars = pkg.get("environmentVariables", [])
        secret_vars = [v["name"] for v in env_vars if v.get("isSecret")]
        required_vars = [v["name"] for v in env_vars if v.get("isRequired")]
        if secret_vars:
            credentials = ", ".join(secret_vars)
        elif required_vars:
            credentials = ", ".join(required_vars)

    # Check remotes if no packages
    remotes = server.get("remotes", [])
    if remotes and not packages:
        transport = remotes[0].get("type", "streamable-http")

    # Use title if available, fall back to name
    display_name = server.get("title", name)

    return {
        "name": display_name,
        "description": description,
        "transport": transport,
        "install": install,
        "credentials": credentials,
        "source": "mcp-registry",
    }


def _parse_smithery_server(entry: dict) -> dict | None:
    """Parse a server entry from the Smithery API."""
    name = entry.get("displayName") or entry.get("qualifiedName", "")
    description = entry.get("description", "")
    if not name or not description:
        return None

    remote = entry.get("remote")
    transport = "streamable-http" if remote else "stdio"

    return {
        "name": name,
        "description": description,
        "transport": transport,
        "install": "",
        "credentials": "none",
        "source": "smithery",
    }
