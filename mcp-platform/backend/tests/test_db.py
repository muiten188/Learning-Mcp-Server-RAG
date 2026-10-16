"""Database pool configuration checks."""

import pytest
from pydantic import ValidationError
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import Settings, get_settings
from app.core.db import engine


def test_async_engine_uses_configured_queue_pool() -> None:
    """Keep the API engine on the async queue pool with bounded connections."""
    assert isinstance(engine.pool, AsyncAdaptedQueuePool)
    assert engine.pool.size() == get_settings().db_pool_size


@pytest.mark.parametrize(
    ("key", "value"),
    [("db_pool_size", 0), ("db_max_overflow", -1), ("db_pool_timeout", 0)],
)
def test_invalid_pool_settings_are_rejected(key: str, value: int) -> None:
    """Reject pool values that cannot be used by SQLAlchemy."""
    with pytest.raises(ValidationError):
        Settings(**{key: value})
