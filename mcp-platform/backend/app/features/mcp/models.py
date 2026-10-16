"""Internal MCP tool result model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResult:
    """Text returned by an MCP tool and its error state."""

    content: str
    is_error: bool
