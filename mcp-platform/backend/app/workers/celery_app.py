# Celery does not ship typing metadata; this import is checked at runtime.
from celery import Celery  # type: ignore[import-untyped]

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "mcp_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.features.documents.tasks"],
)
