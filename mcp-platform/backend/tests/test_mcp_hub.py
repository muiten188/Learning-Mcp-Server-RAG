"""HTTP MCP hub discovery and routing checks."""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Self
from unittest.mock import patch

import pytest

from app.features.mcp.hub import MCPHub, MCPServerSpec, server_specs


@asynccontextmanager
async def fake_transport(url: str) -> AsyncIterator[tuple[str, str, None]]:
    """Stand in for a remote Streamable HTTP connection."""
    if "missing" in url:
        raise OSError("server unavailable")
    yield url, url, None


class FakeSession:
    """Return distinct tools for two remote MCP endpoints."""

    def __init__(self, url: str, writer: str) -> None:
        self.url = url

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def initialize(self) -> None:
        """Accept the test connection."""

    async def list_tools(self) -> SimpleNamespace:
        """Return a tool owned by the selected server."""
        name = "list_files" if "files" in self.url else "database_tables"
        return SimpleNamespace(
            tools=[
                SimpleNamespace(
                    name=name, description=name, input_schema={"type": "object"}
                )
            ]
        )

    async def call_tool(self, name: str, args: dict[str, object]) -> SimpleNamespace:
        """Identify the endpoint that received a routed tool call."""
        return SimpleNamespace(
            content=[SimpleNamespace(text=f"{self.url}: {name}")], is_error=False
        )


def test_hub_routes_http_tools_and_isolates_unavailable_servers() -> None:
    """A failed remote server does not hide healthy servers or their tools."""
    specs = [
        MCPServerSpec(name="files", url="http://files:8000/mcp"),
        MCPServerSpec(name="missing", url="http://missing:8000/mcp"),
        MCPServerSpec(name="database", url="http://database:8000/mcp"),
    ]

    async def check() -> None:
        with (
            patch("app.features.mcp.hub.server_specs", return_value=specs),
            patch("app.features.mcp.hub.streamable_http_client", fake_transport),
            patch("app.features.mcp.hub.ClientSession", FakeSession),
        ):
            async with MCPHub() as hub:
                assert [(item.name, item.status) for item in hub.statuses] == [
                    ("files", "connected"),
                    ("missing", "disconnected"),
                    ("database", "connected"),
                ]
                names = {tool["function"]["name"] for tool in hub.tools}
                assert {"files__list_files", "database__database_tables"} <= names
                assert "files:8000" in (await hub.call("files__list_files", {})).content
                assert (
                    "database:8000"
                    in (await hub.call("database__database_tables", {})).content
                )
                with pytest.raises(ValueError, match="not available"):
                    await hub.call("missing__anything", {})

    asyncio.run(check())


def test_local_registry_uses_http_urls() -> None:
    """Use the same distinct ports for host and container MCP endpoints."""
    expected = {
        "files": 8101,
        "weather": 8102,
        "database": 8103,
        "documents": 8104,
        "web": 8105,
    }
    assert {spec.name: spec.url for spec in server_specs()} == {
        name: f"http://127.0.0.1:{port}/mcp" for name, port in expected.items()
    }
    registry = Path(__file__).resolve().parents[2] / "mcp_servers.container.json"
    container_specs = json.loads(registry.read_text(encoding="utf-8"))
    assert {spec["name"]: spec["url"] for spec in container_specs} == {
        name: f"http://mcp-{name}:{port}/mcp" for name, port in expected.items()
    }
