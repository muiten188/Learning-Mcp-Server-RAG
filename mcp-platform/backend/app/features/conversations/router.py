"""HTTP routes for conversation history."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.features.conversations.schemas import ConversationDetail, ConversationSummary
from app.features.conversations.service import (
    ConversationNotFoundError,
    ConversationService,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
async def conversations(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConversationSummary]:
    """List recent conversations for the sidebar."""
    return await ConversationService(db).list_recent()


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def conversation(
    conversation_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> ConversationDetail:
    """Load one conversation and its messages."""
    try:
        return await ConversationService(db).get_detail(conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(404, "Conversation not found") from exc


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID, db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """Delete one conversation."""
    try:
        await ConversationService(db).delete(conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(404, "Conversation not found") from exc
