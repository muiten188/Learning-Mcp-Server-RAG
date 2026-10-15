"""Background job status HTTP route."""

from fastapi import APIRouter

from app.features.jobs.schemas import JobStatus
from app.features.jobs.service import get_job_status

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatus)
async def job(job_id: str) -> JobStatus:
    """Return a document ingestion task's current Celery state."""
    return get_job_status(job_id)
