"""MCP server discovery API routes."""

import logging

from fastapi import APIRouter, HTTPException

from recommender.mcp_registry import MCPRegistryClient

logger = logging.getLogger(__name__)
router = APIRouter()

_registry = MCPRegistryClient()


@router.get("/servers")
async def list_mcp_servers():
    """List all known MCP servers."""
    return await _registry.get_all()


@router.get("/search")
async def search_mcp_servers(q: str = ""):
    """Search for MCP servers."""
    results = await _registry.search(q)
    return results


@router.get("/servers/{name}")
async def get_mcp_server(name: str):
    """Get details about a specific MCP server."""
    all_servers = await _registry.get_all()
    for server in all_servers:
        if server["name"] == name:
            return server
    raise HTTPException(status_code=404, detail=f"Server '{name}' not found")
