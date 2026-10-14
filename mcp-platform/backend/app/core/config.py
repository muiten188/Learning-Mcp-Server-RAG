from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR.parent / ".env", extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://mcp:mcp@localhost:5432/mcp"
    redis_url: str = "redis://localhost:6379/0"
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"
    mcp_server_script: str = "../servers/tools.py"
    upload_dir: str = "../uploads"

    @property
    def server_path(self) -> Path:
        return (BACKEND_DIR / self.mcp_server_script).resolve()

    @property
    def upload_path(self) -> Path:
        return (BACKEND_DIR / self.upload_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
