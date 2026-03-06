"""Dependency injection for FastAPI routes.

Manages Orchestrator instances per Being, caching them so that
multiple API calls to the same Being reuse the same instance.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from serhu_api.config import Settings

if TYPE_CHECKING:
    from serhu_orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton application settings."""
    return Settings()


# In-memory cache of Orchestrator instances keyed by being_id.
_orchestrators: dict[str, "Orchestrator"] = {}


def _make_llm_client(settings: Settings):
    """Create an OpenAI LLM client if an API key is configured."""
    if not settings.openai_api_key:
        return None
    from serhu_orchestrator.llm.openai_client import OpenAIClient

    return OpenAIClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )


def create_being_orchestrator(
    name: str,
    language: str = "en",
    settings: Settings | None = None,
) -> "Orchestrator":
    """Create a new Being and return its Orchestrator.

    The Orchestrator is cached for subsequent lookups by being_id.
    """
    from serhu_orchestrator.orchestrator import Orchestrator

    logger.info(f"🆕 Creating new Being: name={name!r}, language={language!r}")
    s = settings or get_settings()

    orch = Orchestrator(
        qdrant_url=s.qdrant_url,
        qdrant_api_key=s.qdrant_api_key,
        supabase_url=s.supabase_url,
        supabase_key=s.supabase_key,
        being_name=name,
        language=language,
        llm_client=_make_llm_client(s),
    )

    _orchestrators[orch.being_id] = orch
    logger.info(f"✓ Being created successfully: being_id={orch.being_id}")
    return orch


def get_orchestrator(
    being_id: str,
    settings: Settings | None = None,
) -> "Orchestrator":
    """Return an Orchestrator for the given being_id.

    If the Orchestrator is already cached, return it directly.
    Otherwise, load the Being from the database.

    Raises
    ------
    KeyError
        If the Being cannot be loaded.
    """
    if being_id in _orchestrators:
        logger.info(f"♻️  Using cached Orchestrator for being_id={being_id}")
        return _orchestrators[being_id]

    logger.info(f"📂 Loading Being from database: being_id={being_id}")
    from serhu_orchestrator.orchestrator import Orchestrator

    s = settings or get_settings()

    orch = Orchestrator(
        qdrant_url=s.qdrant_url,
        qdrant_api_key=s.qdrant_api_key,
        supabase_url=s.supabase_url,
        supabase_key=s.supabase_key,
        being_id=being_id,
        llm_client=_make_llm_client(s),
    )

    _orchestrators[being_id] = orch
    logger.info(f"✓ Being loaded successfully: being_id={being_id}")
    return orch


def clear_cache() -> None:
    """Clear the Orchestrator cache (for testing)."""
    logger.info(f"🧹 Clearing orchestrator cache ({len(_orchestrators)} entries)")
    _orchestrators.clear()
    get_settings.cache_clear()
    logger.info("✓ Cache cleared")
