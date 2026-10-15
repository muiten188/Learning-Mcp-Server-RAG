"""Model catalog use case."""

from app.core.config import get_settings
from app.features.models.schemas import ModelsResponse
from app.integrations.ollama.client import Ollama


async def list_models() -> ModelsResponse:
    """List installed Ollama models and the configured default."""
    return ModelsResponse(
        models=await Ollama().models(), default=get_settings().default_model
    )
