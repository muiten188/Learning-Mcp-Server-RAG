import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import get_settings
from app.features.mcp.contracts import ToolDefinition
from app.integrations.ollama.schemas import (
    ChatMessage,
    ChatResponse,
    EmbedResponse,
    ModelListResponse,
    StreamResponse,
)


class Ollama:
    """Call the configured Ollama API for chat, embeddings, and model listing."""

    def __init__(self) -> None:
        self.base_url = get_settings().ollama_base_url.rstrip("/")

    async def chat(
        self,
        model: str,
        messages: list[ChatMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> ChatMessage:
        """Request one non-streamed assistant message from Ollama."""
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        message.model_dump(exclude_none=True) for message in messages
                    ],
                    "tools": tools or [],
                    "stream": False,
                },
            )
            response.raise_for_status()
            return ChatResponse.model_validate(response.json()).message

    async def stream(
        self, model: str, messages: list[ChatMessage]
    ) -> AsyncIterator[str]:
        """Yield assistant text tokens from Ollama's streaming chat API."""
        async with (
            httpx.AsyncClient(timeout=180) as client,
            client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        message.model_dump(exclude_none=True) for message in messages
                    ],
                    "stream": True,
                },
            ) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    item = StreamResponse.model_validate(json.loads(line))
                    if item.error:
                        raise RuntimeError(item.error)
                    if item.message:
                        yield item.message.content

    async def embed(self, text: str) -> list[float]:
        """Create an embedding with the configured model."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={"model": get_settings().embedding_model, "input": text},
            )
            response.raise_for_status()
            return EmbedResponse.model_validate(response.json()).embeddings[0]

    async def models(self) -> list[str]:
        """List model names installed in Ollama."""
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            payload = ModelListResponse.model_validate(response.json())
            return [item.name for item in payload.models]
