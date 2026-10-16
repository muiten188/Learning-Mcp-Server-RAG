"""Conversation use cases and response mapping."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.conversations.models import Conversation, Message, ToolCall
from app.features.conversations.repository import ConversationRepository
from app.features.conversations.schemas import (
    ConversationDetail,
    ConversationSummary,
    MessageResponse,
    ToolCallResponse,
)
from app.features.mcp.contracts import ToolInvocation
from app.integrations.ollama.schemas import ChatMessage


class ConversationNotFoundError(Exception):
    """A requested conversation does not exist."""


class ConversationService:
    """Manage conversation history and messages."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = ConversationRepository(session)

    async def start_chat(
        self, message: str, model: str, conversation_id: UUID | None
    ) -> UUID:
        """Append a user message, creating a conversation if necessary."""
        if conversation_id is not None:
            conversation = await self._repository.get(conversation_id)
            if conversation is None:
                raise ConversationNotFoundError
        else:
            conversation = Conversation(title=message[:80], model=model)
            self._repository.add(conversation)
            await self._session.flush()
        self._repository.add_message(
            Message(conversation_id=conversation.id, role="user", content=message)
        )
        await self._session.commit()
        return conversation.id

    async def list_recent(self) -> list[ConversationSummary]:
        """Return conversation summaries in reverse creation order."""
        rows = await self._repository.list_recent()
        return [
            ConversationSummary(
                id=row.id,
                title=row.title,
                model=row.model,
                created_at=row.created_at,
            )
            for row in rows
        ]

    async def load_chat_history(self, conversation_id: UUID) -> list[ChatMessage]:
        """Load the last 20 persisted messages for an Ollama request.

        Raises:
            ConversationNotFoundError: If the conversation no longer exists.
        """
        row = await self._repository.get_for_chat(conversation_id)
        if row is None:
            raise ConversationNotFoundError
        return [
            ChatMessage(role=message.role, content=message.content)
            for message in row.messages[-20:]
        ]

    async def save_assistant(
        self, conversation_id: UUID, answer: str, calls: list[ToolInvocation]
    ) -> UUID:
        """Persist an assistant answer and its completed tool calls."""
        assistant = Message(
            conversation_id=conversation_id, role="assistant", content=answer
        )
        self._repository.add_message(assistant)
        await self._session.flush()
        for call in calls:
            self._repository.add_tool_call(
                ToolCall(
                    message_id=assistant.id,
                    tool_name=call["name"],
                    arguments=call["arguments"],
                    result=call["result"],
                    is_error=call["is_error"],
                )
            )
        await self._session.commit()
        return assistant.id

    async def get_detail(self, conversation_id: UUID) -> ConversationDetail:
        """Return a conversation and its full history.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        row = await self._repository.get_with_messages(conversation_id)
        if row is None:
            raise ConversationNotFoundError
        return ConversationDetail(
            id=row.id,
            title=row.title,
            model=row.model,
            messages=[
                MessageResponse(
                    id=message.id,
                    role=message.role,
                    content=message.content,
                    tool_calls=[
                        ToolCallResponse(
                            id=call.id,
                            name=call.tool_name,
                            arguments=call.arguments,
                            content=call.result,
                            is_error=call.is_error,
                        )
                        for call in message.tool_calls
                    ],
                )
                for message in row.messages
            ],
        )

    async def delete(self, conversation_id: UUID) -> None:
        """Delete a conversation and its dependent messages.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        row = await self._repository.get(conversation_id)
        if row is None:
            raise ConversationNotFoundError
        await self._repository.delete(row)
        await self._session.commit()
