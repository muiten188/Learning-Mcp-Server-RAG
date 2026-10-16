"""MCP server status use case."""

from app.features.mcp.hub import MCPHub
from app.features.mcp.schemas import MCPServerStatus


async def server_status() -> list[MCPServerStatus]:
    """Discover tools and report each configured MCP server's status."""
    async with MCPHub() as hub:
        return hub.statuses
