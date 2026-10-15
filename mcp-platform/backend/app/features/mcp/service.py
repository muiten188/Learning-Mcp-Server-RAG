"""MCP server status use case."""

from app.features.mcp.client import ollama_tools, tool_session
from app.features.mcp.schemas import MCPServerStatus


async def server_status() -> list[MCPServerStatus]:
    """Discover tools and report the configured MCP server's status."""
    try:
        async with tool_session() as session:
            tools = await ollama_tools(session)
        return [
            MCPServerStatus(
                name="tools",
                status="connected",
                tools=[tool["function"]["name"] for tool in tools],
            )
        ]
    except Exception as exc:  # noqa: BLE001
        # Server failures are part of this status endpoint's response contract.
        return [
            MCPServerStatus(
                name="tools", status="disconnected", error=str(exc), tools=[]
            )
        ]
