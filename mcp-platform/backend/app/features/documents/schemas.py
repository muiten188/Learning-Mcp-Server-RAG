"""Document upload and listing response contracts."""

from uuid import UUID

from pydantic import BaseModel


class DocumentStatus(BaseModel):
    """Public document ingestion state."""

    id: UUID
    filename: str
    status: str
    error: str | None = None


class UploadResponse(BaseModel):
    """Response when an upload is queued for ingestion."""

    id: UUID
    job_id: str
    status: str


class PendingIngestionResponse(BaseModel):
    """Batch enqueue result for pending documents."""

    queued: int
    job_ids: list[str]
