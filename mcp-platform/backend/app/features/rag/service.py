from sqlalchemy.ext.asyncio import AsyncSession

from app.features.rag.repository import has_chunks, nearest_chunks
from app.integrations.ollama.client import Ollama


def chunks(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks for embedding.

    Args:
        text: Source text.
        size: Maximum characters per chunk.
        overlap: Characters repeated between adjacent chunks.

    Returns:
        Non-empty chunks in source order.
    """
    text = text.strip()
    if not text:
        return []
    return [text[start : start + size] for start in range(0, len(text), size - overlap)]


async def retrieve(
    db: AsyncSession, query: str, ollama: Ollama, limit: int = 4
) -> list[tuple[str, str]]:
    """Retrieve ready document chunks nearest to a query embedding.

    Args:
        db: Database session for retrieval.
        query: User query to embed.
        ollama: Embedding client.
        limit: Maximum matching chunks.

    Returns:
        Filename and content pairs ordered by vector distance.
    """
    if not await has_chunks(db):
        return []
    vector = await ollama.embed(query)
    return await nearest_chunks(db, vector, limit)
