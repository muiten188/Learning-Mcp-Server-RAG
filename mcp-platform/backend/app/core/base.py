"""Shared SQLAlchemy registry and timestamp default."""

from datetime import UTC, datetime

from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    """Return the current UTC time for database defaults."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base class for feature-owned database models."""
