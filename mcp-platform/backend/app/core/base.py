"""Shared SQLAlchemy registry and timestamp default."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Return the current UTC time for database defaults."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Shared UUID identity and audit fields for feature-owned models."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    created_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
