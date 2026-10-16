"""Conversation, message, and tool call persistence models."""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.core.json_types import JsonValue


class Conversation(Base):
    """Persist a chat conversation and its selected model."""

    __tablename__ = "conversations"
    title: Mapped[str] = mapped_column(String(160))
    model: Mapped[str] = mapped_column(String(120))
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """Persist a user or assistant message."""

    __tablename__ = "messages"
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    tool_calls: Mapped[list["ToolCall"]] = relationship(
        cascade="all, delete-orphan", order_by="ToolCall.created_at"
    )


class ToolCall(Base):
    """Persist a tool invocation attached to an assistant message."""

    __tablename__ = "tool_calls"
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), index=True
    )
    tool_name: Mapped[str] = mapped_column(String(120))
    arguments: Mapped[dict[str, JsonValue]] = mapped_column(JSONB)
    result: Mapped[str] = mapped_column(Text)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
