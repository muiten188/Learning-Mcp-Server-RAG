"""Document workflow MCP server using the FastAPI document API."""

import os
from uuid import UUID

import httpx
from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, TypeAdapter

mcp = MCPServer("documents")


class DocumentStatus(BaseModel):
    """Document identifier, filename, and ingestion state from FastAPI."""

    id: UUID
    filename: str
    status: str
    error: str | None = None


class PendingIngestion(BaseModel):
    """Job IDs returned when pending documents are queued."""

    queued: int
    job_ids: list[str]


def _api_url() -> str:
    return os.environ.get("BACKEND_API_URL", "http://localhost:8000").rstrip("/")


@mcp.tool()
async def list_documents() -> str:
    """List uploaded document names and their ingestion states.

    Returns:
        One document summary per line, or an error message.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{_api_url()}/api/documents")
            response.raise_for_status()
        rows = TypeAdapter(list[DocumentStatus]).validate_python(response.json())
        return (
            "\n".join(f"{row.id}: {row.filename} ({row.status})" for row in rows)
            or "No documents"
        )
    except httpx.HTTPError as exc:
        return f"Document API error: {exc}"


@mcp.tool()
async def document_status(document_id: str) -> str:
    """Get one document's ingestion state by UUID.

    Args:
        document_id: UUID of an uploaded document.

    Returns:
        Filename and status or an error message.
    """
    try:
        identifier = UUID(document_id)
    except ValueError:
        return "Invalid document UUID"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"{_api_url()}/api/documents/{identifier}")
            if response.status_code == 404:
                return "Document not found"
            response.raise_for_status()
        row = DocumentStatus.model_validate(response.json())
        return f"{row.filename}: {row.status}"
    except httpx.HTTPError as exc:
        return f"Document API error: {exc}"


@mcp.tool()
async def embed_pending_documents() -> str:
    """Queue ingestion for pending documents when the user asks for it.

    Returns:
        Number of queued documents and Celery job IDs, or an error message.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{_api_url()}/api/documents/embed-pending")
            response.raise_for_status()
        result = PendingIngestion.model_validate(response.json())
        return f"Queued {result.queued} documents: {', '.join(result.job_ids)}"
    except httpx.HTTPError as exc:
        return f"Document API error: {exc}"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(
            os.environ.get("MCP_DOCUMENTS_PORT", os.environ.get("MCP_PORT", "8104"))
        ),
        stateless_http=True,
    )
