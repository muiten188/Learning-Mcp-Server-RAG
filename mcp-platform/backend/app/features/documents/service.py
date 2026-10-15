"""Document validation, storage, and listing use cases."""

import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.features.documents.models import Document
from app.features.documents.repository import DocumentRepository
from app.features.documents.schemas import (
    DocumentStatus,
    PendingIngestionResponse,
    UploadResponse,
)
from app.features.documents.tasks import ingest_document

MAX_DOCUMENT_BYTES = 2_000_000


class UnsupportedDocumentError(ValueError):
    """The uploaded filename has an unsupported extension."""


class DocumentTooLargeError(ValueError):
    """The uploaded document exceeds the configured size limit."""


class DocumentEncodingError(ValueError):
    """The uploaded document is not valid UTF-8 text."""


class DocumentService:
    """Validate documents and coordinate persistence with ingestion jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = DocumentRepository(session)

    async def upload(self, filename: str, data: bytes) -> UploadResponse:
        """Store a document and enqueue its ingestion task.

        Args:
            filename: User-provided filename, reduced to a basename.
            data: Uploaded text bytes.

        Returns:
            Document and Celery job identifiers.

        Raises:
            UnsupportedDocumentError: If the extension is unsupported.
            DocumentTooLargeError: If the upload exceeds 2 MB.
            DocumentEncodingError: If the contents are not UTF-8.
        """
        safe_name = Path(filename).name
        if not safe_name.lower().endswith((".txt", ".md")):
            raise UnsupportedDocumentError("Only .txt and .md files are supported")
        if len(data) > MAX_DOCUMENT_BYTES:
            raise DocumentTooLargeError("Maximum document size is 2 MB")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentEncodingError("Document must be UTF-8") from exc

        row = Document(filename=safe_name, storage_path="")
        self._repository.add(row)
        await self._session.flush()
        path = get_settings().upload_path / f"{row.id}.txt"
        await asyncio.to_thread(path.write_bytes, data)
        row.storage_path = str(path)
        await self._session.commit()
        job = ingest_document.delay(str(row.id))
        return UploadResponse(id=row.id, job_id=job.id, status="pending")

    async def list_recent(self) -> list[DocumentStatus]:
        """List documents and their ingestion states."""
        rows = await self._repository.list_recent()
        return [
            DocumentStatus(
                id=row.id,
                filename=row.filename,
                status=row.status,
                error=row.error,
            )
            for row in rows
        ]

    async def queue_pending(self) -> PendingIngestionResponse:
        """Send every pending document to the existing Celery ingestion task."""
        ids = await self._repository.pending_ids()
        jobs = [ingest_document.delay(str(document_id)) for document_id in ids]
        return PendingIngestionResponse(
            queued=len(jobs), job_ids=[job.id for job in jobs]
        )
