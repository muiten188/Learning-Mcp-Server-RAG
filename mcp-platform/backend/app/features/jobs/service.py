"""Celery job status use case."""

from app.features.documents.tasks import ingest_document
from app.features.jobs.schemas import JobStatus


def get_job_status(job_id: str) -> JobStatus:
    """Return the current state and optional error of an ingestion task."""
    result = ingest_document.AsyncResult(job_id)
    return JobStatus(
        id=job_id,
        status=result.status,
        error=str(result.result) if result.failed() else None,
    )
