"""Registry-backed connections to independent MCP servers."""

import json
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Self

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from pydantic import BaseModel, Field, TypeAdapter

from app.core.config import get_settings
from app.core.json_types import JsonValue
from app.features.mcp.client import call_tool
from app.features.mcp.contracts import ToolDefinition
from app.features.mcp.models import ToolResult
from app.features.mcp.schemas import MCPServerStatus


class MCPServerSpec(BaseModel):
    """One enabled or disabled HTTP MCP server in the registry."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    url: str = Field(pattern=r"^https?://[^/]+(?:/.*)?$")
    enabled: bool = True


@dataclass(frozen=True)
class ToolRoute:
    """A discovered tool and the session that owns it."""

    server: str
    name: str
    session: ClientSession


def server_specs() -> list[MCPServerSpec]:
    """Load and validate the HTTP MCP registry.

    Returns:
        Server specifications in registry order.

    Raises:
        ValueError: If server names are duplicated.
    """
    settings = get_settings()
    if not settings.servers_path.exists():
        raise FileNotFoundError(f"MCP registry not found: {settings.servers_path}")
    specs = TypeAdapter(list[MCPServerSpec]).validate_python(
        json.loads(settings.servers_path.read_text(encoding="utf-8"))
    )
    names = [spec.name for spec in specs]
    if len(names) != len(set(names)):
        raise ValueError("MCP server names must be unique")
    return specs


class MCPHub:
    """Connect configured servers and route qualified tool calls."""

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._routes: dict[str, ToolRoute] = {}
        self.tools: list[ToolDefinition] = []
        self.statuses: list[MCPServerStatus] = []

    async def __aenter__(self) -> Self:
        """Connect enabled servers and discover their tools."""
        try:
            for spec in server_specs():
                if not spec.enabled:
                    self.statuses.append(
                        MCPServerStatus(name=spec.name, status="disabled", tools=[])
                    )
                    continue
                try:
                    async with AsyncExitStack() as server_stack:
                        transport = await server_stack.enter_async_context(
                            streamable_http_client(spec.url)
                        )
                        reader, writer = transport[0], transport[1]
                        session = await server_stack.enter_async_context(
                            ClientSession(reader, writer)
                        )
                        await session.initialize()
                        discovered = await session.list_tools()
                        tool_names: list[str] = []
                        routes: dict[str, ToolRoute] = {}
                        definitions: list[ToolDefinition] = []
                        for tool in discovered.tools:
                            alias = f"{spec.name}__{tool.name}"
                            routes[alias] = ToolRoute(spec.name, tool.name, session)
                            tool_names.append(tool.name)
                            definitions.append(
                                ToolDefinition(
                                    type="function",
                                    function={
                                        "name": alias,
                                        "description": tool.description or "",
                                        "parameters": TypeAdapter(
                                            dict[str, JsonValue]
                                        ).validate_python(tool.input_schema),
                                    },
                                )
                            )
                        self._stack.push_async_callback(server_stack.pop_all().aclose)
                    self._routes.update(routes)
                    self.tools.extend(definitions)
                    self.statuses.append(
                        MCPServerStatus(
                            name=spec.name, status="connected", tools=tool_names
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    self.statuses.append(
                        MCPServerStatus(
                            name=spec.name,
                            status="disconnected",
                            tools=[],
                            error=str(exc),
                        )
                    )
            return self
        except BaseException:
            await self._stack.aclose()
            raise

    async def __aexit__(self, *exc_info: object) -> None:
        """Close all server sessions and HTTP connections."""
        await self._stack.aclose()

    def server_for(self, alias: str) -> str:
        """Find the owning server for a discovered tool.

        Raises:
            ValueError: If the requested tool was not discovered.
        """
        if alias not in self._routes:
            raise ValueError(f"Tool is not available for this request: {alias}")
        return self._routes[alias].server

    async def call(self, alias: str, arguments: dict[str, JsonValue]) -> ToolResult:
        """Call a discovered tool on its owning server.

        Raises:
            ValueError: If the requested tool was not discovered.
        """
        self.server_for(alias)
        route = self._routes[alias]
        return await call_tool(route.session, route.name, arguments)
