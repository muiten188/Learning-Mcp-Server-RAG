from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Typed configuration loaded from the platform environment."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR.parent / ".env", extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://mcp:mcp@localhost:5432/mcp"
    db_pool_size: int = Field(default=5, gt=0)
    db_max_overflow: int = Field(default=10, ge=0)
    db_pool_timeout: int = Field(default=30, gt=0)
    redis_url: str = "redis://localhost:6379/0"
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"
    mcp_servers_file: str = "../mcp_servers.json"
    upload_dir: str = "../uploads"

    @property
    def servers_path(self) -> Path:
        """Resolve the MCP server registry relative to the backend."""
        return (BACKEND_DIR / self.mcp_servers_file).resolve()

    @property
    def upload_path(self) -> Path:
        """Resolve the configured upload directory relative to the backend."""
        return (BACKEND_DIR / self.upload_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    """Return the cached backend settings instance."""
    return Settings()
