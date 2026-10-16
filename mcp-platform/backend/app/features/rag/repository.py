"""Vector similarity query for ready document chunks."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.documents.models import Document, DocumentChunk
from app.features.rag.schemas import RetrievedChunk


async def nearest_chunks(
    db: AsyncSession, vector: list[float], limit: int
) -> list[RetrievedChunk]:
    """Return filename and text pairs nearest to an embedding."""
    stmt = (
        select(Document.filename, DocumentChunk.content)
        .join(DocumentChunk, Document.id == DocumentChunk.document_id)
        .where(Document.status == "ready")
        .order_by(DocumentChunk.embedding.cosine_distance(vector))
        .limit(limit)
    )
    return [
        RetrievedChunk(filename=filename, content=content)
        for filename, content in (await db.execute(stmt)).all()
    ]


async def has_chunks(db: AsyncSession) -> bool:
    """Report whether any document chunks exist before embedding a query."""
    return await db.scalar(select(DocumentChunk.id).limit(1)) is not None
