"""Shared ORM metadata checks."""

from sqlalchemy import DateTime, Uuid

from app.core.base import Base
from app.features.conversations.models import Conversation, Message, ToolCall  # noqa: F401
from app.features.documents.models import Document, DocumentChunk  # noqa: F401


def test_all_entities_inherit_uuid_and_audit_columns() -> None:
    """Keep the shared fields on every persisted entity, including chunks."""
    assert set(Base.metadata.tables) == {
        "conversations",
        "messages",
        "tool_calls",
        "documents",
        "document_chunks",
    }
    for table in Base.metadata.tables.values():
        columns = table.columns
        assert {"id", "created_by", "created_at", "updated_by", "updated_at"} <= set(
            columns.keys()
        )
        assert isinstance(columns["id"].type, Uuid)
        assert columns["id"].primary_key
        assert columns["id"].default is not None
        assert isinstance(columns["created_by"].type, Uuid)
        assert isinstance(columns["updated_by"].type, Uuid)
        assert columns["created_by"].nullable
        assert columns["updated_by"].nullable
        assert isinstance(columns["created_at"].type, DateTime)
        assert isinstance(columns["updated_at"].type, DateTime)
        assert columns["updated_at"].onupdate is not None
