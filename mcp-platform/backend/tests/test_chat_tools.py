"""LLM driven MCP tool selection checks."""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Self
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.features.chat.orchestrator import run_chat
from app.features.mcp.contracts import ToolDefinition
from app.features.mcp.models import ToolResult
from app.integrations.ollama.schemas import (
    ChatMessage,
    RequestedFunction,
    RequestedToolCall,
)

TOOLS: list[ToolDefinition] = [
    {
        "type": "function",
        "function": {
            "name": "web__crawl_webpage",
            "description": "Read a web page",
            "parameters": {"type": "object", "properties": {"url": {"type": "string"}}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weather__get_weather",
            "description": "Get weather",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
            },
        },
    },
]


@asynccontextmanager
async def fake_session() -> AsyncIterator[SimpleNamespace]:
    """Provide a session-shaped object without an external service."""
    yield SimpleNamespace(rollback=AsyncMock())


async def fake_stream(model: str, messages: list[ChatMessage]) -> AsyncIterator[str]:
    """Return one token from a stubbed Ollama stream."""
    yield "Answer"


@pytest.mark.parametrize(
    "requested_name", [None, "web__crawl_webpage", "weather__get_weather"]
)
def test_model_decides_whether_to_call_a_discovered_tool(
    requested_name: str | None,
) -> None:
    """Offer all discovered tools and execute only the model's valid choice."""
    conversation_id = uuid4()
    message_id = uuid4()
    response = ChatMessage(role="assistant")
    if requested_name:
        response.tool_calls = [
            RequestedToolCall(
                function=RequestedFunction(
                    name=requested_name,
                    arguments={"url": "https://example.com"}
                    if requested_name == "web__crawl_webpage"
                    else {"city": "Hanoi"},
                )
            )
        ]
    ollama = SimpleNamespace(
        chat=AsyncMock(side_effect=[response, ChatMessage(role="assistant")]),
        stream=fake_stream,
    )
    conversations = SimpleNamespace(
        load_chat_history=AsyncMock(
            return_value=[ChatMessage(role="user", content="help")]
        ),
        save_assistant=AsyncMock(return_value=message_id),
    )
    invoke = AsyncMock(return_value=ToolResult(content="result", is_error=False))

    class FakeHub:
        """Expose the configured test tools through the hub interface."""

        tools = TOOLS

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *exc_info: object) -> None:
            return None

        def server_for(self, name: str) -> str:
            return name.split("__", 1)[0]

        async def call(self, name: str, arguments: dict[str, object]) -> ToolResult:
            return await invoke(name, arguments)

    async def check() -> list[dict[str, object]]:
        with (
            patch("app.features.chat.orchestrator.Ollama", return_value=ollama),
            patch("app.features.chat.orchestrator.SessionLocal", fake_session),
            patch(
                "app.features.chat.orchestrator.ConversationService",
                return_value=conversations,
            ),
            patch(
                "app.features.chat.orchestrator.retrieve", AsyncMock(return_value=[])
            ),
            patch("app.features.chat.orchestrator.MCPHub", FakeHub),
        ):
            events = [item async for item in run_chat(conversation_id, "model", "help")]
        return [json.loads(item.split("data: ", 1)[1]) for item in events]

    events = asyncio.run(check())
    assert ollama.chat.call_args.args[2] == TOOLS
    if requested_name:
        invoke.assert_awaited_once()
        assert invoke.call_args.args[0] == requested_name
        assert any(item.get("name") == requested_name for item in events)
    else:
        invoke.assert_not_awaited()
    assert events[-1]["model"] == "model"
