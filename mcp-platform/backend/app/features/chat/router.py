"""Streaming chat HTTP route."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.features.chat.orchestrator import run_chat
from app.features.chat.schemas import ChatRequest
from app.features.conversations.service import (
    ConversationNotFoundError,
    ConversationService,
)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(
    body: ChatRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> StreamingResponse:
    """Save a user message and stream the assistant's SSE response."""
    model = body.model or get_settings().default_model
    try:
        conversation_id = await ConversationService(db).start_chat(
            body.message, model, body.conversation_id
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(404, "Conversation not found") from exc
    return StreamingResponse(
        run_chat(conversation_id, model, body.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
