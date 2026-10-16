"""Named contracts for MCP tools and saved invocations."""

from typing import Literal, TypedDict

from app.core.json_types import JsonValue


class ToolFunction(TypedDict):
    """Ollama function description created from an MCP tool."""

    name: str
    description: str
    parameters: dict[str, JsonValue]


class ToolDefinition(TypedDict):
    """Ollama tool definition."""

    type: Literal["function"]
    function: ToolFunction


class ToolInvocation(TypedDict):
    """Completed tool call saved with an assistant message."""

    name: str
    arguments: dict[str, JsonValue]
    result: str
    is_error: bool
