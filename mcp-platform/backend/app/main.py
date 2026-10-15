"""FastAPI application setup and health endpoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.db import engine
from app.features.chat.router import router as chat_router
from app.features.conversations.router import router as conversations_router
from app.features.documents.router import router as documents_router
from app.features.jobs.router import router as jobs_router
from app.features.mcp.router import router as mcp_router
from app.features.models.router import router as models_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Prepare upload storage and dispose of database connections on shutdown."""
    get_settings().upload_path.mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(
    title="MCP Platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(mcp_router)
app.include_router(models_router)


@app.get("/docs", include_in_schema=False)
async def legacy_docs() -> RedirectResponse:
    """Keep the original backend Swagger URL working."""
    return RedirectResponse(url="/api/docs")


@app.get("/health")
async def health() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}
