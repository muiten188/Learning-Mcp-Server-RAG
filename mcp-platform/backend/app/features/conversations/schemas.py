"""Public conversation response contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.json_types import JsonValue


class ToolCallResponse(BaseModel):
    """Tool call details attached to an assistant message."""

    id: UUID
    name: str
    arguments: dict[str, JsonValue]
    content: str
    is_error: bool


class MessageResponse(BaseModel):
    """A persisted conversation message."""

    id: UUID
    role: str
    content: str
    tool_calls: list[ToolCallResponse]


class ConversationSummary(BaseModel):
    """Conversation metadata shown in the sidebar."""

    id: UUID
    title: str
    model: str
    created_at: datetime


class ConversationDetail(BaseModel):
    """Conversation metadata and full message history."""

    id: UUID
    title: str
    model: str
    messages: list[MessageResponse]
