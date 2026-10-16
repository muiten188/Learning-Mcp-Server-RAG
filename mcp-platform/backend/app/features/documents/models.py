"""Document and vector chunk persistence models."""

from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base


class Document(Base):
    """Persist an uploaded or seeded document."""

    __tablename__ = "documents"
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunks: Mapped[list["DocumentChunk"]] = relationship(cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Persist searchable document text and its embedding."""

    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index"),)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(768))
