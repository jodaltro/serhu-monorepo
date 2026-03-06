"""Application settings loaded from environment variables.

Uses pydantic-settings for type-safe configuration with .env file support.
All external service credentials are centralised here.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# Resolve the monorepo root regardless of where uvicorn is launched from.
# config.py lives at packages/api/src/serhu_api/config.py → 4 levels up = root.
_MONOREPO_ROOT = Path(__file__).resolve().parents[4]
_ENV_FILE = str(_MONOREPO_ROOT / ".env")


class Settings(BaseSettings):
    """SerHu API configuration.

    Values are read from environment variables or a ``.env`` file.
    """

    # -- Qdrant (Vector Memory) ----------------------------------------------
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description="Qdrant cluster endpoint",
    )
    qdrant_api_key: str = Field(
        default="",
        description="Qdrant API key",
    )

    # -- Supabase (Relational Memory) ----------------------------------------
    supabase_url: str = Field(
        default="http://localhost:54321",
        description="Supabase project URL",
    )
    supabase_key: str = Field(
        default="",
        description="Supabase anon/service key",
    )

    # -- OpenAI (LLM) -------------------------------------------------------
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (optional — enables chat and enhanced sleep)",
    )
    openai_model: str = Field(
        default="gpt-5.4",
        description="OpenAI model identifier",
    )

    # -- API server ----------------------------------------------------------
    api_host: str = Field(default="0.0.0.0", description="API listen host")
    api_port: int = Field(default=8000, description="API listen port")
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    model_config = {
        "env_file": _ENV_FILE,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
