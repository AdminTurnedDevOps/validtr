"""Tests for MCPRegistryClient — fetching from upstream registries."""

import pytest

from recommender.mcp_registry import MCPRegistryClient, _parse_official_server, _parse_smithery_server


# --- Sample data matching real API responses ---

SAMPLE_OFFICIAL_ENTRY = {
    "server": {
        "name": "io.example/postgres-server",
        "description": "PostgreSQL database access and management",
        "title": "Postgres MCP Server",
        "version": "1.0.0",
        "packages": [
            {
                "registryType": "npm",
                "identifier": "@example/mcp-postgres",
                "runtimeHint": "npx -y",
                "transport": {"type": "stdio"},
                "environmentVariables": [
                    {"name": "DATABASE_URL", "isRequired": True, "isSecret": True},
                ],
            }
        ],
    },
    "_meta": {},
}

SAMPLE_OFFICIAL_REMOTE_ONLY = {
    "server": {
        "name": "io.example/remote-api",
        "description": "Remote API server with no local packages",
        "version": "1.0.0",
        "remotes": [
            {"type": "streamable-http", "url": "https://api.example.com/mcp"}
        ],
    },
    "_meta": {},
}

SAMPLE_SMITHERY_ENTRY = {
    "qualifiedName": "example/browser-tool",
    "displayName": "Browser Tool",
    "description": "Browser automation for testing and scraping",
    "remote": True,
    "useCount": 500,
}


class TestParseOfficialServer:
    """Tests for parsing official MCP registry entries."""

    def test_parses_full_entry(self):
        result = _parse_official_server(SAMPLE_OFFICIAL_ENTRY)
        assert result is not None
        assert result["name"] == "Postgres MCP Server"
        assert result["description"] == "PostgreSQL database access and management"
        assert result["transport"] == "stdio"
        assert result["install"] == "npx -y @example/mcp-postgres"
        assert result["credentials"] == "DATABASE_URL"
        assert result["source"] == "mcp-registry"

    def test_parses_remote_only_entry(self):
        result = _parse_official_server(SAMPLE_OFFICIAL_REMOTE_ONLY)
        assert result is not None
        assert result["transport"] == "streamable-http"
        assert result["install"] == ""
        assert result["credentials"] == "none"

    def test_returns_none_for_empty(self):
        assert _parse_official_server({"server": {}}) is None
        assert _parse_official_server({"server": {"name": "x"}}) is None
        assert _parse_official_server({"server": {"description": "y"}}) is None


class TestParseSmitheryServer:
    """Tests for parsing Smithery API entries."""

    def test_parses_entry(self):
        result = _parse_smithery_server(SAMPLE_SMITHERY_ENTRY)
        assert result is not None
        assert result["name"] == "Browser Tool"
        assert result["description"] == "Browser automation for testing and scraping"
        assert result["transport"] == "streamable-http"
        assert result["source"] == "smithery"

    def test_stdio_when_not_remote(self):
        entry = {**SAMPLE_SMITHERY_ENTRY, "remote": False}
        result = _parse_smithery_server(entry)
        assert result["transport"] == "stdio"

    def test_returns_none_for_empty(self):
        assert _parse_smithery_server({}) is None
        assert _parse_smithery_server({"displayName": "x"}) is None


class TestMCPRegistryClientGetRelevant:
    """Tests for get_relevant() filtering."""

    @pytest.fixture
    def client_with_cache(self):
        """Client with pre-populated cache to avoid real HTTP calls."""
        client = MCPRegistryClient()
        client._cache = [
            {"name": "postgres", "description": "PostgreSQL database access", "transport": "stdio", "install": "npx -y @mcp/postgres", "credentials": "DATABASE_URL", "source": "mcp-registry"},
            {"name": "auth0", "description": "Authentication and OAuth JWT management", "transport": "stdio", "install": "npx -y auth0-mcp", "credentials": "AUTH0_DOMAIN", "source": "mcp-registry"},
            {"name": "fetch", "description": "Fetch web pages and REST APIs", "transport": "stdio", "install": "npx -y @mcp/fetch", "credentials": "none", "source": "mcp-registry"},
            {"name": "filesystem", "description": "Read write and search files", "transport": "stdio", "install": "npx -y @mcp/filesystem", "credentials": "none", "source": "mcp-registry"},
        ]
        client._cache_time = 9999999999.0  # far future so cache doesn't expire
        return client

    @pytest.mark.asyncio
    async def test_returns_relevant_servers(self, client_with_cache):
        results = await client_with_cache.get_relevant("database postgres")
        assert len(results) >= 1
        assert results[0]["name"] == "postgres"

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_match(self, client_with_cache):
        results = await client_with_cache.get_relevant("xyznonexistent12345")
        assert results == []

    @pytest.mark.asyncio
    async def test_respects_limit(self, client_with_cache):
        results = await client_with_cache.get_relevant("", limit=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_scores_name_higher_than_description(self, client_with_cache):
        results = await client_with_cache.get_relevant("auth0")
        assert results[0]["name"] == "auth0"


class TestMCPRegistryClientSearch:
    """Tests for search() with mocked upstream calls."""

    @pytest.fixture
    def client_with_cache(self):
        client = MCPRegistryClient()
        client._cache = [
            {"name": "postgres", "description": "PostgreSQL database", "transport": "stdio", "install": "", "credentials": "DATABASE_URL", "source": "mcp-registry"},
            {"name": "filesystem", "description": "File read write search", "transport": "stdio", "install": "", "credentials": "none", "source": "mcp-registry"},
        ]
        client._cache_time = 9999999999.0
        return client

    @pytest.mark.asyncio
    async def test_falls_back_to_cached_filter(self, client_with_cache, monkeypatch):
        """When both upstream searches fail, falls back to filtering cache."""

        async def _empty_official(self, query):
            return []

        async def _empty_smithery(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_official", _empty_official)
        monkeypatch.setattr(MCPRegistryClient, "_search_smithery", _empty_smithery)

        results = await client_with_cache.search("postgres")
        assert len(results) >= 1
        assert any(r["name"] == "postgres" for r in results)

    @pytest.mark.asyncio
    async def test_search_no_match_returns_empty(self, client_with_cache, monkeypatch):
        async def _empty_official(self, query):
            return []

        async def _empty_smithery(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_official", _empty_official)
        monkeypatch.setattr(MCPRegistryClient, "_search_smithery", _empty_smithery)

        results = await client_with_cache.search("xyznonexistent12345")
        assert results == []
