"""Relational Memory – Supabase relational store.

Implements the structured-data tier of the MemGPT-like architecture.
Stores the Being's personality ledger, episodic event logs, and semantic
facts in relational tables for deterministic queries.

References:
    - MemGPT episodic/semantic memory: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - Supabase Python client: https://supabase.com/docs/reference/python/introduction
"""

from __future__ import annotations

import json
import time

from supabase import create_client, Client


class RelationalMemory:
    """Structured relational memory backed by Supabase.

    Manages three logical tables:
    - ``personality_ledger`` – the Being's current personality state
    - ``episodic_log`` – timestamped interaction episodes
    - ``semantic_facts`` – consolidated knowledge extracted from episodes

    Parameters
    ----------
    url : str
        Supabase project URL.
    key : str
        Supabase anon/service key.
    """

    TABLE_PERSONALITY = "personality_ledger"
    TABLE_EPISODES = "episodic_log"
    TABLE_FACTS = "semantic_facts"

    def __init__(self, url: str, key: str) -> None:
        self._client: Client = create_client(url, key)

    # -- personality ledger --------------------------------------------------

    def save_personality(self, being_id: str, state_json: dict) -> dict:
        """Upsert the Being's personality state.

        Parameters
        ----------
        being_id : str
            Unique identifier for the Being.
        state_json : dict
            The full PersonalityState as a JSON-serializable dict.

        Returns
        -------
        dict
            The upserted row.
        """
        row = {
            "being_id": being_id,
            "state": json.dumps(state_json),
            "updated_at": time.time(),
        }
        result = (
            self._client.table(self.TABLE_PERSONALITY)
            .upsert(row, on_conflict="being_id")
            .execute()
        )
        return result.data[0] if result.data else row

    def load_personality(self, being_id: str) -> dict | None:
        """Load the Being's personality state.

        Returns
        -------
        dict | None
            The parsed PersonalityState dict, or ``None`` if not found.
        """
        result = (
            self._client.table(self.TABLE_PERSONALITY)
            .select("*")
            .eq("being_id", being_id)
            .execute()
        )
        if not result.data:
            return None
        return json.loads(result.data[0]["state"])

    # -- episodic log --------------------------------------------------------

    def log_episode(
        self,
        being_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> dict:
        """Append an interaction episode.

        Parameters
        ----------
        being_id : str
            Being identifier.
        role : str
            Speaker role (user | being | system).
        content : str
            The message content.
        metadata : dict | None
            Optional metadata (sentiment, topic, etc.).

        Returns
        -------
        dict
            The inserted row.
        """
        row = {
            "being_id": being_id,
            "role": role,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "created_at": time.time(),
        }
        result = (
            self._client.table(self.TABLE_EPISODES)
            .insert(row)
            .execute()
        )
        return result.data[0] if result.data else row

    def get_episodes(
        self,
        being_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve recent episodes for a Being.

        Returns
        -------
        list[dict]
            Episodes ordered by creation time (newest first).
        """
        result = (
            self._client.table(self.TABLE_EPISODES)
            .select("*")
            .eq("being_id", being_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    # -- semantic facts ------------------------------------------------------

    def store_fact(
        self,
        being_id: str,
        fact: str,
        source_episode_ids: list[str] | None = None,
    ) -> dict:
        """Store a consolidated semantic fact.

        Parameters
        ----------
        being_id : str
            Being identifier.
        fact : str
            The distilled knowledge statement.
        source_episode_ids : list[str] | None
            References to episodic log entries that originated this fact.

        Returns
        -------
        dict
            The inserted row.
        """
        row = {
            "being_id": being_id,
            "fact": fact,
            "source_episodes": json.dumps(source_episode_ids or []),
            "created_at": time.time(),
        }
        result = (
            self._client.table(self.TABLE_FACTS)
            .insert(row)
            .execute()
        )
        return result.data[0] if result.data else row

    def get_facts(self, being_id: str, limit: int = 100) -> list[dict]:
        """Retrieve semantic facts for a Being.

        Returns
        -------
        list[dict]
            Facts ordered by creation time (newest first).
        """
        result = (
            self._client.table(self.TABLE_FACTS)
            .select("*")
            .eq("being_id", being_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
