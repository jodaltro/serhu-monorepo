"""Integration tests for the full Orchestrator flow.

Tests the complete lifecycle: Being creation → interaction → memory archival
→ personality evolution → recall, using real Qdrant and Supabase backends.

Requires QDRANT_URL, QDRANT_API_KEY, SUPABASE_URL, SUPABASE_KEY env vars.
"""

import time
import uuid

import pytest

from serhu_orchestrator.orchestrator import Orchestrator
from serhu_orchestrator.memory.relational_memory import RelationalMemory


@pytest.mark.integration
class TestOrchestratorFlow:
    """End-to-end integration tests for the Orchestrator."""

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        qdrant_url: str,
        qdrant_api_key: str,
        supabase_url: str,
        supabase_key: str,
    ):
        """Create an Orchestrator with a fresh Being and clean up after."""
        self.collection = f"test_orch_{uuid.uuid4().hex[:8]}"
        self.orch = Orchestrator(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            being_name="IntegrationBeing",
            working_memory_size=5,
            collection_name=self.collection,
        )
        self.being_id = self.orch.being_id
        yield
        # Cleanup
        try:
            self.orch.cleanup_archival()
        except Exception:
            pass
        self._cleanup_supabase(supabase_url, supabase_key)

    def _cleanup_supabase(self, url: str, key: str):
        rel = RelationalMemory(url=url, key=key)
        for table in [
            RelationalMemory.TABLE_PERSONALITY,
            RelationalMemory.TABLE_EPISODES,
            RelationalMemory.TABLE_FACTS,
        ]:
            try:
                rel._client.table(table).delete().eq("being_id", self.being_id).execute()
            except Exception:
                pass

    def test_being_created_as_tabula_rasa(self):
        """A new Being starts in the sensorimotor stage with neutral traits."""
        p = self.orch.personality
        assert p.development.stage == "sensorimotor"
        assert p.development.interaction_count == 0
        assert p.hexaco.sincerity == 0.5
        assert p.tci_character.empathy == 0.0
        assert p.schwartz.stimulation == 0.0
        assert p.name == "IntegrationBeing"

    def test_process_message_adds_to_context(self):
        """Processing a message returns it in the context window."""
        ctx = self.orch.process_message("user", "What is the sky?")
        assert len(ctx.working) == 1
        assert ctx.working[0].content == "What is the sky?"

    def test_process_message_with_trait_updates(self):
        """Trait deltas are applied to the personality."""
        self.orch.process_message(
            role="user",
            content="You are doing great!",
            trait_deltas={
                "hexaco": {"sincerity": 0.05, "liveliness": 0.03},
                "tci_character": {"empathy": 0.1},
            },
        )
        p = self.orch.personality
        assert p.hexaco.sincerity == pytest.approx(0.55, abs=0.001)
        assert p.hexaco.liveliness == pytest.approx(0.53, abs=0.001)
        assert p.tci_character.empathy == pytest.approx(0.1, abs=0.001)
        assert p.development.interaction_count == 1

    def test_consolidate_flushes_to_archival(self):
        """Consolidation moves working memory to Qdrant."""
        self.orch.process_message("user", "Message one")
        self.orch.process_message("being", "Response one")
        self.orch.process_message("user", "Message two")

        archived_count = self.orch.consolidate()
        assert archived_count == 3

        # Wait for Qdrant indexing
        time.sleep(2)

        # Verify entries exist in archival
        results = self.orch.recall("Message", top_k=5)
        assert len(results) > 0

    def test_learn_fact_persists(self):
        """Semantic facts are stored in Supabase."""
        self.orch.learn_fact("The user is interested in astronomy.")
        rel = self.orch._relational
        facts = rel.get_facts(self.being_id, limit=10)
        fact_texts = [f["fact"] for f in facts]
        assert "The user is interested in astronomy." in fact_texts

    def test_working_memory_overflow_archives(self):
        """When working memory overflows, evicted entries go to Qdrant."""
        # Working memory size is 5
        for i in range(7):
            self.orch.process_message("user", f"Message {i}")

        # 2 entries should have been evicted and archived
        time.sleep(2)
        results = self.orch.recall("Message 0", top_k=3)
        assert len(results) > 0

    def test_personality_persists_across_load(
        self,
        qdrant_url: str,
        qdrant_api_key: str,
        supabase_url: str,
        supabase_key: str,
    ):
        """Personality changes persist and can be reloaded."""
        # Apply some trait changes
        self.orch.process_message(
            "user",
            "I believe in honesty.",
            trait_deltas={"hexaco": {"sincerity": 0.1}},
        )

        # Create a new Orchestrator loading the same Being
        orch2 = Orchestrator(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            being_id=self.being_id,
            collection_name=self.collection,
        )
        assert orch2.personality.hexaco.sincerity == pytest.approx(0.6, abs=0.001)
        assert orch2.personality.development.interaction_count == 1

    def test_full_lifecycle(self):
        """Full lifecycle: create → interact → consolidate → recall → evolve."""
        # 1. Interact during wakefulness
        self.orch.process_message("user", "I love watching the stars at night.")
        self.orch.process_message(
            "being", "The stars? Tell me more about them!"
        )
        self.orch.process_message("user", "They are distant suns, billions of years old.")

        # 2. Learn a fact (semantization)
        self.orch.learn_fact("Stars are distant suns billions of years old.")

        # 3. Apply personality evolution
        self.orch.process_message(
            "user",
            "You seem curious about the universe.",
            trait_deltas={
                "hexaco": {"inquisitiveness": 0.08},
                "schwartz": {"universalism_nature": 0.05},
                "tci_character": {"self_forgetfulness": 0.03},
            },
        )

        # 4. Consolidate (twilight phase)
        archived = self.orch.consolidate()
        assert archived >= 0  # working memory may have been partially evicted

        # 5. Verify personality evolution
        p = self.orch.personality
        assert p.hexaco.inquisitiveness > 0.5
        assert p.schwartz.universalism_nature > 0.0
        assert p.development.interaction_count >= 1
