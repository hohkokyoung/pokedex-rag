"""Application configuration.

Settings are loaded from environment variables (and the repository-root `.env`
file during local development). Compose injects the same variables directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root: backend/app/core/config.py -> parents[3] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime settings for the backend."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://pokedex:pokedex@db:5432/pokedex",
        description="Async SQLAlchemy connection URL.",
    )

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # CORS — comma-separated list of allowed origins.
    cors_origins: str = "http://localhost:3000"

    # Filesystem path to downloaded Pokémon sprites (served as static files).
    sprites_dir: str = str(REPO_ROOT / "data" / "sprites")

    # --- RAG: embeddings ---
    # Local embedding model (fastembed / ONNX — no external API, runs in-process).
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # --- RAG: LLM providers ---
    # Preferred: Anthropic Claude. Fallback: Groq (free tier, OpenAI-compatible).
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    # Retrieval depth for the Ask endpoint.
    rag_top_k: int = 6

    # Ask plans its retrieval with the LLM when a key is set. False = the keyword
    # planner answers every question (the quick switch if LLM planning misbehaves).
    ask_agent_enabled: bool = True

    @property
    def llm_provider(self) -> str:
        """Active provider: 'anthropic' (preferred), else 'groq', else 'none'."""
        if self.anthropic_api_key.strip():
            return "anthropic"
        if self.groq_api_key.strip():
            return "groq"
        return "none"

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider != "none"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
