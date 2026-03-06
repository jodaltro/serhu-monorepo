"""Application settings loaded from environment variables.

Uses pydantic-settings for type-safe configuration with .env file support.
All external service credentials are centralised here.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }
