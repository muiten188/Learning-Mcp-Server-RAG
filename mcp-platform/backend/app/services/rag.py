from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk
from app.services.ollama import Ollama


def chunks(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [text[start : start + size] for start in range(0, len(text), size - overlap)]


async def retrieve(
    db: AsyncSession, query: str, ollama: Ollama, limit: int = 4
) -> list[tuple[str, str]]:
    exists = await db.scalar(select(DocumentChunk.id).limit(1))
    if exists is None:
        return []
    vector = await ollama.embed(query)
    stmt = (
        select(Document.filename, DocumentChunk.content)
        .join(DocumentChunk, Document.id == DocumentChunk.document_id)
        .where(Document.status == "ready")
        .order_by(DocumentChunk.embedding.cosine_distance(vector))
        .limit(limit)
    )
    return list((await db.execute(stmt)).all())
