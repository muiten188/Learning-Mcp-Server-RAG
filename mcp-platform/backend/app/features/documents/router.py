"""Document upload and listing HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.features.documents.schemas import (
    DocumentStatus,
    PendingIngestionResponse,
    UploadResponse,
)
from app.features.documents.service import (
    MAX_DOCUMENT_BYTES,
    DocumentEncodingError,
    DocumentService,
    DocumentTooLargeError,
    UnsupportedDocumentError,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post(
    "/embed-pending",
    response_model=PendingIngestionResponse,
    status_code=202,
    summary="Queue embedding for all pending documents",
)
async def embed_pending_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PendingIngestionResponse:
    """Queue chunking and embedding for all documents with pending status."""
    return await DocumentService(db).queue_pending()


@router.post("", response_model=UploadResponse, status_code=202)
async def upload_document(
    file: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UploadResponse:
    """Accept a UTF-8 text document and queue vector ingestion."""
    data = await file.read(MAX_DOCUMENT_BYTES + 1)
    try:
        return await DocumentService(db).upload(file.filename or "", data)
    except UnsupportedDocumentError as exc:
        raise HTTPException(400, str(exc)) from exc
    except DocumentTooLargeError as exc:
        raise HTTPException(413, str(exc)) from exc
    except DocumentEncodingError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("", response_model=list[DocumentStatus])
async def documents(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentStatus]:
    """List uploaded and seeded documents with their processing states."""
    return await DocumentService(db).list_recent()
