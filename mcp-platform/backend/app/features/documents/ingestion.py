"""Document ingestion and embedding use case."""

import asyncio
from pathlib import Path
from uuid import UUID

from app.core.db import SessionLocal
from app.features.documents.models import DocumentChunk
from app.features.documents.repository import DocumentRepository
from app.features.rag.service import chunks
from app.integrations.ollama.client import Ollama

EMBEDDING_DIMENSION = 768


async def ingest(document_id: UUID) -> None:
    """Read, embed, and persist a document, updating its processing status.

    Args:
        document_id: Identifier of a pending document.

    Raises:
        ValueError: If the text is empty or embedding dimensions differ.
        Exception: If reading, embedding, or persistence fails after status is
            recorded as failed.
    """
    async with SessionLocal() as db:
        repository = DocumentRepository(db)
        document = await repository.get(document_id)
        if document is None:
            return
        try:
            text = await asyncio.to_thread(
                Path(document.storage_path).read_text, encoding="utf-8"
            )
            parts = chunks(text)
            if not parts:
                raise ValueError("Document is empty")
            ollama = Ollama()
            await repository.delete_chunks(document_id)
            for index, part in enumerate(parts):
                vector = await ollama.embed(part)
                if len(vector) != EMBEDDING_DIMENSION:
                    raise ValueError(
                        f"Expected {EMBEDDING_DIMENSION} embedding dimensions, got {len(vector)}"
                    )
                repository.add_chunk(
                    DocumentChunk(
                        document_id=document_id,
                        chunk_index=index,
                        content=part,
                        embedding=vector,
                    )
                )
            document.status = "ready"
            document.error = None
            await db.commit()
        except Exception as exc:
            # Persist the failure after rolling back any partially added chunks.
            await db.rollback()
            document = await repository.get(document_id)
            if document is not None:
                document.status = "failed"
                document.error = str(exc)[:1000]
                await db.commit()
            raise
