import asyncio
from uuid import UUID

from sqlalchemy import delete

from app.core.db import SessionLocal, engine
from app.models import Document, DocumentChunk
from app.services.ollama import Ollama
from app.services.rag import chunks
from app.workers.celery_app import celery_app


async def ingest(document_id: UUID):
    async with SessionLocal() as db:
        document = await db.get(Document, document_id)
        if document is None:
            return
        try:
            from pathlib import Path

            text = Path(document.storage_path).read_text(encoding="utf-8")
            parts = chunks(text)
            if not parts:
                raise ValueError("Document is empty")
            ollama = Ollama()
            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            for index, part in enumerate(parts):
                vector = await ollama.embed(part)
                if len(vector) != 768:
                    raise ValueError(
                        f"Expected 768 embedding dimensions, got {len(vector)}"
                    )
                db.add(
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
            await db.rollback()
            document = await db.get(Document, document_id)
            document.status = "failed"
            document.error = str(exc)[:1000]
            await db.commit()
            raise


@celery_app.task(name="ingest_document")
def ingest_document(document_id: str):
    async def execute():
        await ingest(UUID(document_id))
        await engine.dispose()

    asyncio.run(execute())
