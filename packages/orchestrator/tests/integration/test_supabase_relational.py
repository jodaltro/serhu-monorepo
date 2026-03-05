"""Integration tests for RelationalMemory (Supabase).

These tests require a real Supabase instance with the following tables:
- personality_ledger (being_id TEXT PRIMARY KEY, state TEXT, updated_at FLOAT)
- episodic_log (id SERIAL PRIMARY KEY, being_id TEXT, role TEXT, content TEXT,
                metadata TEXT, created_at FLOAT)
- semantic_facts (id SERIAL PRIMARY KEY, being_id TEXT, fact TEXT,
                  source_episodes TEXT, created_at FLOAT)

Set SUPABASE_URL and SUPABASE_KEY environment variables (or use a .env file).
"""

import json
import uuid

import pytest

from serhu_orchestrator.memory.relational_memory import RelationalMemory
from serhu_orchestrator.personality.types import PersonalityState


@pytest.mark.integration
class TestRelationalMemorySupabase:
    """Integration tests for Supabase-backed relational memory."""

    @pytest.fixture(autouse=True)
    def _setup(self, supabase_url: str, supabase_key: str):
        """Create a RelationalMemory instance and test being_id."""
        self.relational = RelationalMemory(url=supabase_url, key=supabase_key)
        self.being_id = f"test-being-{uuid.uuid4().hex[:8]}"
        yield
        # Cleanup: delete test data
        self._cleanup()

    def _cleanup(self):
        """Best-effort cleanup of test data."""
        try:
            self.relational._client.table(RelationalMemory.TABLE_PERSONALITY).delete().eq(
                "being_id", self.being_id
            ).execute()
        except Exception:
            pass
        try:
            self.relational._client.table(RelationalMemory.TABLE_EPISODES).delete().eq(
                "being_id", self.being_id
            ).execute()
        except Exception:
            pass
        try:
            self.relational._client.table(RelationalMemory.TABLE_FACTS).delete().eq(
                "being_id", self.being_id
            ).execute()
        except Exception:
            pass

    def test_save_and_load_personality(self):
        """Save a PersonalityState and reload it."""
        state = PersonalityState(being_id=self.being_id, name="TestBeing")
        state_dict = state.model_dump()

        self.relational.save_personality(self.being_id, state_dict)
        loaded = self.relational.load_personality(self.being_id)

        assert loaded is not None
        assert loaded["being_id"] == self.being_id
        assert loaded["name"] == "TestBeing"
        assert loaded["hexaco"]["sincerity"] == 0.5

    def test_load_personality_not_found(self):
        """Loading a nonexistent Being returns None."""
        loaded = self.relational.load_personality("nonexistent-being-xyz")
        assert loaded is None

    def test_log_and_get_episodes(self):
        """Log episodes and retrieve them."""
        self.relational.log_episode(
            being_id=self.being_id,
            role="user",
            content="Hello, I am your creator.",
            metadata={"sentiment": 0.9},
        )
        self.relational.log_episode(
            being_id=self.being_id,
            role="being",
            content="Hello! What is this place?",
            metadata={"sentiment": 0.7},
        )

        episodes = self.relational.get_episodes(self.being_id, limit=10)
        assert len(episodes) >= 2
        # Newest first
        contents = [e["content"] for e in episodes]
        assert "Hello! What is this place?" in contents
        assert "Hello, I am your creator." in contents

    def test_store_and_get_facts(self):
        """Store semantic facts and retrieve them."""
        self.relational.store_fact(
            being_id=self.being_id,
            fact="The user values creativity and freedom.",
        )
        self.relational.store_fact(
            being_id=self.being_id,
            fact="Loud noises cause discomfort to the user.",
        )

        facts = self.relational.get_facts(self.being_id, limit=10)
        assert len(facts) >= 2
        fact_texts = [f["fact"] for f in facts]
        assert "The user values creativity and freedom." in fact_texts

    def test_personality_upsert_updates_existing(self):
        """Upserting personality updates the existing record."""
        state = PersonalityState(being_id=self.being_id, name="V1")
        self.relational.save_personality(self.being_id, state.model_dump())

        state.name = "V2"
        state.hexaco.sincerity = 0.8
        self.relational.save_personality(self.being_id, state.model_dump())

        loaded = self.relational.load_personality(self.being_id)
        assert loaded["name"] == "V2"
        assert loaded["hexaco"]["sincerity"] == 0.8
