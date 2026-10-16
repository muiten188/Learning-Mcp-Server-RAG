from mcp import ClientSession

from app.core.json_types import JsonValue
from app.features.mcp.models import ToolResult


async def call_tool(
    session: ClientSession, name: str, args: dict[str, JsonValue]
) -> ToolResult:
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
    return ToolResult(content=content or "(no output)", is_error=bool(result.is_error))
