"""MCP server discovery API routes."""

import logging

from fastapi import APIRouter, HTTPException

from recommender.mcp_registry import CURATED_MCP_SERVERS, MCPRegistryClient

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/servers")
async def list_mcp_servers():
    """List all known MCP servers."""
    return CURATED_MCP_SERVERS


@router.get("/search")
async def search_mcp_servers(q: str = ""):
    """Search for MCP servers."""
    client = MCPRegistryClient()
    results = await client.search(q)
    return results


@router.get("/servers/{name}")
async def get_mcp_server(name: str):
    """Get details about a specific MCP server."""
    for server in CURATED_MCP_SERVERS:
        if server["name"] == name:
            return server
    raise HTTPException(status_code=404, detail=f"Server '{name}' not found")
