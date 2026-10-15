"""MCP server status response contract."""

from pydantic import BaseModel


class MCPServerStatus(BaseModel):
    """Connection state and tool names for an MCP server."""

    name: str
    status: str
    tools: list[str]
    error: str | None = None
