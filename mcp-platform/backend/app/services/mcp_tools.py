"""Compatibility imports for the feature-owned MCP client."""

from app.features.mcp.client import call_tool, ollama_tools, tool_session

__all__ = ["call_tool", "ollama_tools", "tool_session"]
