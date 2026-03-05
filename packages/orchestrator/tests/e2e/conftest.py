"""Shared fixtures for local end-to-end tests.

Provides in-memory replacements for ArchivalMemory and RelationalMemory
so the full Orchestrator lifecycle can be exercised without Qdrant or
Supabase credentials.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from unittest.mock import patch

import pytest

from serhu_orchestrator.memory.archival_memory import ArchivalEntry


# ---------------------------------------------------------------------------
# In-memory backends
# ---------------------------------------------------------------------------


class InMemoryRelational:
    """Drop-in replacement for RelationalMemory backed by plain dicts."""

    TABLE_PERSONALITY = "personality_ledger"
    TABLE_EPISODES = "episodic_log"
    TABLE_FACTS = "semantic_facts"

    def __init__(self, url: str = "", key: str = "") -> None:
        self._personalities: dict[str, dict] = {}
        self._episodes: list[dict] = []
        self._facts: list[dict] = []

    # -- personality ledger --------------------------------------------------

    def save_personality(self, being_id: str, state_json: dict) -> dict:
        row = {
            "being_id": being_id,
            "state": json.dumps(state_json) if isinstance(state_json, dict) else state_json,
            "updated_at": time.time(),
        }
        self._personalities[being_id] = row
        return row

    def load_personality(self, being_id: str) -> dict | None:
        row = self._personalities.get(being_id)
        if row is None:
            return None
        state = row["state"]
        return json.loads(state) if isinstance(state, str) else state

    # -- episodic log --------------------------------------------------------

    def log_episode(
        self,
        being_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        entry = {
            "being_id": being_id,
            "role": role,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "created_at": time.time(),
        }
        self._episodes.append(entry)
        return entry

    def get_episodes(self, being_id: str, limit: int = 50) -> list[dict]:
        matching = [e for e in self._episodes if e["being_id"] == being_id]
        return matching[-limit:]

    # -- semantic facts ------------------------------------------------------

    def store_fact(
        self,
        being_id: str,
        fact: str,
        source_episode_ids: list[int] | None = None,
    ) -> dict:
        entry = {
            "being_id": being_id,
            "fact": fact,
            "source_episodes": json.dumps(source_episode_ids or []),
            "created_at": time.time(),
        }
        self._facts.append(entry)
        return entry

    def get_facts(self, being_id: str, limit: int = 100) -> list[dict]:
        matching = [f for f in self._facts if f["being_id"] == being_id]
        return matching[-limit:]


class InMemoryArchival:
    """Drop-in replacement for ArchivalMemory backed by a plain list."""

    def __init__(
        self,
        url: str = "",
        api_key: str = "",
        collection_name: str = "test",
        vector_size: int = 384,
    ) -> None:
        self._entries: list[ArchivalEntry] = []

    def store(self, entry: ArchivalEntry) -> str:
        self._entries.append(entry)
        return entry.entry_id

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[dict]:
        filtered = self._entries
        if memory_type:
            filtered = [e for e in filtered if e.memory_type == memory_type]
        results = []
        for e in filtered[-top_k:]:
            results.append({
                "content": e.content,
                "score": 0.9,
                "memory_type": e.memory_type,
                "metadata": e.metadata or {},
            })
        return results

    def delete_collection(self) -> None:
        self._entries.clear()

    def count(self) -> int:
        return len(self._entries)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_orchestrator():
    """Create an Orchestrator with in-memory backends (no external services).

    Patches ArchivalMemory and RelationalMemory constructors so the
    Orchestrator can be instantiated with dummy URLs.

    Yields
    ------
    Orchestrator
        A fully functional orchestrator using in-memory storage.
    """
    from serhu_orchestrator.orchestrator import Orchestrator

    with (
        patch(
            "serhu_orchestrator.orchestrator.ArchivalMemory",
            InMemoryArchival,
        ),
        patch(
            "serhu_orchestrator.orchestrator.RelationalMemory",
            InMemoryRelational,
        ),
    ):
        orch = Orchestrator(
            qdrant_url="mock://qdrant",
            qdrant_api_key="mock-key",
            supabase_url="mock://supabase",
            supabase_key="mock-key",
            being_name="E2E-Being",
            language="pt",
            working_memory_size=10,
        )
        yield orch


@pytest.fixture()
def mock_orchestrator_en():
    """Same as mock_orchestrator but with English language."""
    from serhu_orchestrator.orchestrator import Orchestrator

    with (
        patch(
            "serhu_orchestrator.orchestrator.ArchivalMemory",
            InMemoryArchival,
        ),
        patch(
            "serhu_orchestrator.orchestrator.RelationalMemory",
            InMemoryRelational,
        ),
    ):
        orch = Orchestrator(
            qdrant_url="mock://qdrant",
            qdrant_api_key="mock-key",
            supabase_url="mock://supabase",
            supabase_key="mock-key",
            being_name="E2E-Being-EN",
            language="en",
            working_memory_size=10,
        )
        yield orch
