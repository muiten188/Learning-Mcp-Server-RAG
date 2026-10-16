"""API contract checks that do not require external services."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import httpx

from app.features.documents.service import DocumentService
from app.main import app


def test_routes_and_health() -> None:
    """Keep the public route paths stable while organizing routers by feature."""
    paths = app.openapi()["paths"]
    assert {
        "/health",
        "/api/chat",
        "/api/conversations",
        "/api/conversations/{conversation_id}",
        "/api/models",
        "/api/mcp-servers",
        "/api/documents",
        "/api/documents/embed-pending",
        "/api/jobs/{job_id}",
    } <= paths.keys()

    async def check() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    asyncio.run(check())


def test_swagger_and_openapi_are_available() -> None:
    """Serve the interactive API reference and its schema."""

    async def check() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            docs = await client.get("/api/docs")
            schema = await client.get("/api/openapi.json")
            legacy_docs = await client.get("/docs")
        assert docs.status_code == 200
        assert "Swagger UI" in docs.text
        assert schema.status_code == 200
        assert "/api/documents/embed-pending" in schema.json()["paths"]
        assert legacy_docs.status_code == 307
        assert legacy_docs.headers["location"] == "/api/docs"

    asyncio.run(check())


def test_embed_pending_queues_each_pending_document() -> None:
    """Batch ingestion enqueues pending IDs and reports the resulting jobs."""
    document_ids = [uuid4(), uuid4()]
    service = DocumentService.__new__(DocumentService)
    service._repository = SimpleNamespace(
        pending_ids=AsyncMock(return_value=document_ids)
    )

    with patch(
        "app.features.documents.service.ingest_document.delay",
        side_effect=[SimpleNamespace(id="job-1"), SimpleNamespace(id="job-2")],
    ) as enqueue:
        result = asyncio.run(service.queue_pending())

    assert result.queued == 2
    assert result.job_ids == ["job-1", "job-2"]
    assert [call.args[0] for call in enqueue.call_args_list] == [
        str(document_id) for document_id in document_ids
    ]


def test_remaining_legacy_python_imports_remain_available() -> None:
    """Keep the remaining compatibility imports usable by external scripts."""
    from app.features.conversations.models import Conversation
    from app.features.documents.tasks import ingest_document
    from app.models import Conversation as LegacyConversation
    from app.workers.tasks import ingest_document as legacy_ingest_document

    assert LegacyConversation is Conversation
    assert legacy_ingest_document is ingest_document


def test_upload_rejects_unsupported_text() -> None:
    """Reject invalid document input before accessing the database or broker."""

    async def check() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            invalid_extension = await client.post(
                "/api/documents", files={"file": ("file.pdf", b"hello")}
            )
            invalid_encoding = await client.post(
                "/api/documents", files={"file": ("file.txt", b"\xff")}
            )
            oversized = await client.post(
                "/api/documents",
                files={"file": ("file.txt", b"a" * 2_000_001)},
            )
        assert invalid_extension.status_code == 400
        assert invalid_encoding.status_code == 400
        assert oversized.status_code == 413

    asyncio.run(check())
