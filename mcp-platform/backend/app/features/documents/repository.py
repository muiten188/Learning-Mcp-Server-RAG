"""Database operations for documents and chunks."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.documents.models import Document, DocumentChunk


class DocumentRepository:
    """Access documents and chunks within a caller-owned session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, document_id: UUID) -> Document | None:
        """Find one document by ID."""
        return await self._session.get(Document, document_id)

    async def get_by_filename(self, filename: str) -> UUID | None:
        """Find a document ID by its filename."""
        return await self._session.scalar(
            select(Document.id).where(Document.filename == filename).limit(1)
        )

    async def list_recent(self) -> list[Document]:
        """List documents ordered from newest to oldest."""
        return list(
            (
                await self._session.scalars(
                    select(Document).order_by(Document.created_at.desc())
                )
            ).all()
        )

    async def pending_ids(self) -> list[UUID]:
        """Find documents still waiting for ingestion."""
        return list(
            (
                await self._session.scalars(
                    select(Document.id).where(Document.status == "pending")
                )
            ).all()
        )

    def add(self, document: Document) -> None:
        """Stage a document for insertion."""
        self._session.add(document)

    async def delete_chunks(self, document_id: UUID) -> None:
        """Remove existing chunks before reindexing a document."""
        await self._session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )

    def add_chunk(self, chunk: DocumentChunk) -> None:
        """Stage an embedded document chunk for insertion."""
        self._session.add(chunk)
