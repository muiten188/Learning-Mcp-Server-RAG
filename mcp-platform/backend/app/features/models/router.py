"""Available Ollama models HTTP route."""

import httpx
from fastapi import APIRouter, HTTPException

from app.features.models.schemas import ModelsResponse
from app.features.models.service import list_models

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=ModelsResponse)
async def models() -> ModelsResponse:
    """List installed Ollama models and the configured default."""
    try:
        return await list_models()
    except httpx.HTTPError as exc:
        raise HTTPException(503, "Ollama unavailable") from exc
