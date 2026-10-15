"""Chat request contract."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """User message and optional conversation or model selection."""

    message: str = Field(min_length=1, max_length=12000)
    conversation_id: UUID | None = None
    model: str | None = None
