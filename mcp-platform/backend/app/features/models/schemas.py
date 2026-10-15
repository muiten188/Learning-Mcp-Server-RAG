"""Ollama model listing response contract."""

from pydantic import BaseModel


class ModelsResponse(BaseModel):
    """Installed Ollama models and the configured default."""

    models: list[str]
    default: str
