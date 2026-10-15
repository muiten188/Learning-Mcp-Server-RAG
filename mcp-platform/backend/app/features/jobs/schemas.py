"""Background job status response contract."""

from pydantic import BaseModel


class JobStatus(BaseModel):
    """Celery task state exposed through the API."""

    id: str
    status: str
    error: str | None = None
