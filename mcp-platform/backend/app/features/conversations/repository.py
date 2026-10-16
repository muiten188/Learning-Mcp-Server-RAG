"""Database operations for conversations and messages."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.conversations.models import Conversation, Message, ToolCall


class ConversationRepository:
    """Persist and load conversations within a caller-owned session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, conversation_id: UUID) -> Conversation | None:
        """Find a conversation by ID without loading messages."""
        return await self._session.scalar(
            select(Conversation).where(Conversation.id == conversation_id)
        )

    async def get_with_messages(self, conversation_id: UUID) -> Conversation | None:
        """Load a conversation with its messages and tool calls."""
        return await self._session.scalar(
            select(Conversation)
            .options(
                selectinload(Conversation.messages).selectinload(Message.tool_calls)
            )
            .where(Conversation.id == conversation_id)
        )

    async def get_for_chat(self, conversation_id: UUID) -> Conversation | None:
        """Load messages needed to build a chat prompt."""
        return await self._session.scalar(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )

    async def list_recent(self) -> list[Conversation]:
        """List conversations ordered from newest to oldest."""
        return list(
            (
                await self._session.scalars(
                    select(Conversation).order_by(Conversation.created_at.desc())
                )
            ).all()
        )

    def add(self, conversation: Conversation) -> None:
        """Stage a conversation for insertion."""
        self._session.add(conversation)

    def add_message(self, message: Message) -> None:
        """Stage a message for insertion."""
        self._session.add(message)

    def add_tool_call(self, call: ToolCall) -> None:
        """Stage a tool call for insertion."""
        self._session.add(call)

    async def delete(self, conversation: Conversation) -> None:
        """Stage a conversation for deletion."""
        await self._session.delete(conversation)
