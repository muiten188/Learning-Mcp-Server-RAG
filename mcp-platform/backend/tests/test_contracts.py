"""Structured backend result and external response checks."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.features.rag.repository import nearest_chunks
from app.features.rag.schemas import RetrievedChunk
from app.features.rag.service import retrieve
from app.integrations.ollama.schemas import ChatResponse, StreamResponse


def test_retrieve_returns_named_chunk_results() -> None:
    """Expose document matches by field name throughout the chat path."""
    db = SimpleNamespace()
    ollama = SimpleNamespace(embed=AsyncMock(return_value=[0.1, 0.2]))
    expected = [RetrievedChunk(filename="guide.md", content="example")]
    with (
        patch("app.features.rag.service.has_chunks", AsyncMock(return_value=True)),
        patch(
            "app.features.rag.service.nearest_chunks", AsyncMock(return_value=expected)
        ),
    ):
        result = asyncio.run(retrieve(db, "example", ollama))
    assert result == expected
    assert result[0].filename == "guide.md"
    assert result[0].content == "example"


def test_repository_maps_rows_to_named_results() -> None:
    """Convert SQLAlchemy rows before they leave the repository."""
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(all=lambda: [("guide.md", "example")])
        )
    )
    result = asyncio.run(nearest_chunks(db, [0.1, 0.2], 4))
    assert result == [RetrievedChunk(filename="guide.md", content="example")]


def test_ollama_responses_have_named_fields() -> None:
    """Parse tool requests and streamed content into explicit models."""
    chat = ChatResponse.model_validate(
        {
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_weather",
                            "arguments": {"city": "Hanoi"},
                        }
                    }
                ],
            }
        }
    )
    assert chat.message.tool_calls[0].function.name == "get_weather"
    assert chat.message.tool_calls[0].function.arguments == {"city": "Hanoi"}
    assert (
        StreamResponse.model_validate(
            {"message": {"role": "assistant", "content": "hello"}}
        ).message.content
        == "hello"
    )
