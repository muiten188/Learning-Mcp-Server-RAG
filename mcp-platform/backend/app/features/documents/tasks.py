"""Celery entry point for document ingestion."""

import asyncio
from uuid import UUID

from app.core.db import engine
from app.features.documents.ingestion import ingest
from app.workers.celery_app import celery_app


@celery_app.task(name="ingest_document")
def ingest_document(document_id: str) -> None:
    """Run document ingestion in a Celery worker process."""

    async def execute() -> None:
        try:
            await ingest(UUID(document_id))
        finally:
            await engine.dispose()

    asyncio.run(execute())
