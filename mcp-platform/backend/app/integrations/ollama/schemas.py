"""Validated Ollama chat response contracts."""

from pydantic import BaseModel, Field

from app.core.json_types import JsonValue


class RequestedFunction(BaseModel):
    """Function call requested by an Ollama model."""

    name: str
    arguments: dict[str, JsonValue] | str = Field(default_factory=dict)


class RequestedToolCall(BaseModel):
    """One function call attached to an assistant message."""

    function: RequestedFunction


class ChatMessage(BaseModel):
    """One Ollama chat message sent or received by the backend."""

    role: str
    content: str = ""
    tool_name: str | None = None
    tool_calls: list[RequestedToolCall] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Ollama response to a non-streamed chat request."""

    message: ChatMessage


class StreamResponse(BaseModel):
    """One line from an Ollama chat stream."""

    message: ChatMessage | None = None
    error: str | None = None


class EmbedResponse(BaseModel):
    """Embedding vectors returned by Ollama."""

    embeddings: list[list[float]]


class ModelInfo(BaseModel):
    """Installed Ollama model name."""

    name: str


class ModelListResponse(BaseModel):
    """Ollama model listing response."""

    models: list[ModelInfo] = Field(default_factory=list)
