"""Tests for MCPRegistryClient and CURATED_MCP_SERVERS."""

import pytest

from recommender.mcp_registry import CURATED_MCP_SERVERS, MCPRegistryClient


class TestCuratedMCPServers:
    """Tests for the CURATED_MCP_SERVERS list."""

    def test_non_empty(self):
        assert len(CURATED_MCP_SERVERS) > 0

    def test_each_entry_has_required_keys(self):
        required_keys = {"name", "transport", "install", "description", "credentials"}
        for entry in CURATED_MCP_SERVERS:
            missing = required_keys - set(entry.keys())
            assert not missing, f"Server '{entry.get('name', '?')}' missing keys: {missing}"

    def test_each_entry_has_capabilities(self):
        for entry in CURATED_MCP_SERVERS:
            assert "capabilities" in entry, f"Server '{entry['name']}' missing capabilities"
            assert isinstance(entry["capabilities"], list)
            assert len(entry["capabilities"]) > 0

    def test_known_servers_present(self):
        names = [s["name"] for s in CURATED_MCP_SERVERS]
        assert "filesystem" in names
        assert "github" in names

    def test_transport_values_valid(self):
        valid_transports = {"stdio", "streamable-http"}
        for entry in CURATED_MCP_SERVERS:
            assert entry["transport"] in valid_transports, (
                f"Server '{entry['name']}' has invalid transport: {entry['transport']}"
            )


class TestMCPRegistryClientSearch:
    """Tests for MCPRegistryClient.search() using the curated fallback."""

    @pytest.fixture
    def client(self):
        return MCPRegistryClient()

    @pytest.mark.asyncio
    async def test_search_matching_name(self, client, monkeypatch):
        # Force _search_online to return empty so we hit curated fallback
        async def _empty_online(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_online", _empty_online)

        results = await client.search("filesystem")
        assert len(results) >= 1
        assert any(r["name"] == "filesystem" for r in results)

    @pytest.mark.asyncio
    async def test_search_matching_description(self, client, monkeypatch):
        async def _empty_online(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_online", _empty_online)

        results = await client.search("browser")
        assert len(results) >= 1
        assert any(r["name"] == "puppeteer" for r in results)

    @pytest.mark.asyncio
    async def test_search_matching_capability(self, client, monkeypatch):
        async def _empty_online(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_online", _empty_online)

        results = await client.search("web-search")
        assert len(results) >= 1
        assert any(r["name"] == "brave-search" for r in results)

    @pytest.mark.asyncio
    async def test_search_no_match(self, client, monkeypatch):
        async def _empty_online(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_online", _empty_online)

        results = await client.search("xyznonexistent12345")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_capabilities_filter(self, client, monkeypatch):
        async def _empty_online(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_online", _empty_online)

        results = await client.search("", capabilities=["file-read"])
        assert len(results) >= 1
        assert any(r["name"] == "filesystem" for r in results)

    @pytest.mark.asyncio
    async def test_search_results_have_source_field(self, client, monkeypatch):
        async def _empty_online(self, query):
            return []

        monkeypatch.setattr(MCPRegistryClient, "_search_online", _empty_online)

        results = await client.search("github")
        for r in results:
            assert r["source"] == "curated"
