"""Compatibility imports for models moved into feature packages."""

from app.core.base import Base, utcnow
from app.features.conversations.models import Conversation, Message, ToolCall
from app.features.documents.models import Document, DocumentChunk

__all__ = [
    "Base",
    "Conversation",
    "Document",
    "DocumentChunk",
    "Message",
    "ToolCall",
    "utcnow",
]
