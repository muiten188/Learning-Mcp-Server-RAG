import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import get_settings


@asynccontextmanager
async def tool_session() -> AsyncIterator[ClientSession]:
    """Open an initialized stdio session with the configured MCP server."""
    path = get_settings().server_path
    params = StdioServerParameters(
        command=sys.executable, args=[str(path)], cwd=str(path.parent)
    )
    async with (
        stdio_client(params) as (reader, writer),
        ClientSession(reader, writer) as session,
    ):
        await session.initialize()
        yield session


async def ollama_tools(session: ClientSession) -> list[dict[str, Any]]:
    """Convert discovered MCP tools to Ollama function definitions.

    Args:
        session: Initialized MCP client session.

    Returns:
        Tool definitions accepted by Ollama.
    """
    result = await session.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in result.tools
    ]


async def call_tool(
    session: ClientSession, name: str, args: dict[str, Any]
) -> tuple[str, bool]:
    """Invoke one MCP tool and return its text and error state.

    Args:
        session: Initialized MCP client session.
        name: Tool name returned by discovery.
        args: Arguments for the tool schema.

    Returns:
        Tool output text and whether MCP marked the call as an error.
    """
    result = await session.call_tool(name, args)
    content = "\n".join(getattr(item, "text", "") for item in result.content)
    return content or "(no output)", bool(result.is_error)
