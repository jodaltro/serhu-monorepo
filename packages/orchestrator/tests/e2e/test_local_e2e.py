"""Local end-to-end tests – full Orchestrator lifecycle without external services.

Exercises the complete Being lifecycle using in-memory ArchivalMemory and
RelationalMemory backends.  No Qdrant or Supabase credentials are required.

Run with:
    python -m pytest packages/orchestrator/tests/e2e -v
"""

from __future__ import annotations

import pytest

from serhu_orchestrator.orchestrator import Orchestrator
from serhu_orchestrator.personality.prompt_builder import build_system_prompt
from serhu_orchestrator.personality.types import (
    PersonalityState,
    STAGE_MILESTONES,
    STAGE_ORDER,
    ERIKSON_CONFLICTS,
)
from serhu_orchestrator.personality.event_store import EventStore
from serhu_orchestrator.personality.proto_converter import (
    personality_to_ledger,
    ledger_to_personality,
)
from serhu_orchestrator.sleep.sleep_cycle import SleepCycle


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------


class TestLocalE2ELifecycle:
    """End-to-end lifecycle without external services."""

    def test_create_being_tabula_rasa(self, mock_orchestrator: Orchestrator):
        """A new Being starts as a blank slate."""
        p = mock_orchestrator.personality
        assert p.name == "E2E-Being"
        assert p.language == "pt"
        assert p.development.stage == "sensorimotor"
        assert p.development.cognitive_age == 0.0
        assert p.development.interaction_count == 0
        assert p.hexaco.sincerity == 0.5
        assert p.tci_character.empathy == 0.0
        assert p.schwartz.stimulation == 0.0
        assert p.core_beliefs == []
        assert p.surface_beliefs == []

    def test_interact_and_evolve_traits(self, mock_orchestrator: Orchestrator):
        """Interactions update traits and increment interaction count."""
        ctx = mock_orchestrator.process_message(
            role="user",
            content="Olá, como vai?",
            trait_deltas={
                "hexaco": {"sociability": 0.1, "sincerity": 0.05},
                "tci_character": {"empathy": 0.08},
                "schwartz": {"benevolence_caring": 0.03},
            },
        )

        # Context window contains the message
        assert len(ctx.working) >= 1
        assert ctx.working[0].content == "Olá, como vai?"

        # Traits evolved
        p = mock_orchestrator.personality
        assert p.hexaco.sociability == pytest.approx(0.6, abs=0.001)
        assert p.hexaco.sincerity == pytest.approx(0.55, abs=0.001)
        assert p.tci_character.empathy == pytest.approx(0.08, abs=0.001)
        assert p.schwartz.benevolence_caring == pytest.approx(0.03, abs=0.001)
        assert p.development.interaction_count == 1

    def test_multiple_interactions_accumulate(self, mock_orchestrator: Orchestrator):
        """Multiple interactions accumulate in working memory."""
        messages = [
            ("user", "Primeira mensagem"),
            ("being", "Resposta do ser"),
            ("user", "Segunda mensagem"),
            ("being", "Segunda resposta"),
        ]
        for role, content in messages:
            ctx = mock_orchestrator.process_message(role, content)

        assert len(ctx.working) == 4

    def test_consolidate_flushes_working_memory(self, mock_orchestrator: Orchestrator):
        """Consolidation moves entries from working to archival memory."""
        mock_orchestrator.process_message("user", "Mensagem 1")
        mock_orchestrator.process_message("being", "Resposta 1")
        mock_orchestrator.process_message("user", "Mensagem 2")

        archived = mock_orchestrator.consolidate()
        assert archived == 3

    def test_sleep_cycle_produces_results(self, mock_orchestrator: Orchestrator):
        """Sleep cycle extracts facts, generates hypotheses, and adds beliefs."""
        # Feed some interactions first
        for i in range(5):
            mock_orchestrator.process_message(
                "user", f"O universo é muito bonito e bonito demais {i}"
            )
            mock_orchestrator.process_message(
                "being", f"Concordo, o universo é bonito e bonito {i}"
            )

        result = mock_orchestrator.sleep(num_rollouts=50, svd_rank=4, seed=42)

        # Sleep cycle produces structured output
        assert isinstance(result.traits_before, list)
        assert isinstance(result.traits_after, list)
        assert len(result.traits_before) == 72  # HEXACO(24)+TCI-T(16)+TCI-C(13)+Schwartz(19)
        assert len(result.traits_after) == 72

    def test_build_prompt_reflects_personality(self, mock_orchestrator: Orchestrator):
        """System prompt reflects the current personality and language."""
        prompt = mock_orchestrator.build_prompt()

        # Portuguese prompt markers
        assert 'language="pt"' in prompt
        assert "E2E-Being" in prompt
        assert "sensorimotor" in prompt
        # Sensorimotor prompt should have output_rules, not personality scores
        assert "<output_rules>" in prompt
        assert "CONFIANÇA" in prompt or "confiança" in prompt.lower()

    def test_build_prompt_english(self, mock_orchestrator_en: Orchestrator):
        """English Being produces English prompts."""
        prompt = mock_orchestrator_en.build_prompt()

        assert 'language="en"' in prompt
        assert "TRUST" in prompt or "trust" in prompt.lower()

    def test_learn_fact_persists(self, mock_orchestrator: Orchestrator):
        """Semantic facts are stored and retrievable."""
        mock_orchestrator.learn_fact("O usuário ama astronomia.")
        facts = mock_orchestrator._relational.get_facts(
            mock_orchestrator.being_id, limit=10
        )
        fact_texts = [f["fact"] for f in facts]
        assert "O usuário ama astronomia." in fact_texts

    def test_recall_returns_archived_entries(self, mock_orchestrator: Orchestrator):
        """Recall retrieves entries from archival memory."""
        # Add and consolidate entries
        mock_orchestrator.process_message("user", "As estrelas são distantes.")
        mock_orchestrator.consolidate()

        results = mock_orchestrator.recall("estrelas", top_k=3)
        assert len(results) > 0

    def test_working_memory_overflow_archives(self, mock_orchestrator: Orchestrator):
        """When working memory overflows, evicted entries go to archival."""
        # Working memory size is 10
        for i in range(12):
            mock_orchestrator.process_message("user", f"Mensagem longa {i}")

        # 2 entries should have been evicted and archived
        archival_count = mock_orchestrator._archival.count()
        assert archival_count >= 2

    def test_full_lifecycle_create_interact_sleep_prompt(
        self, mock_orchestrator: Orchestrator
    ):
        """Complete lifecycle: create → interact → evolve → consolidate → sleep → prompt."""
        orch = mock_orchestrator

        # 1. Interact during wakefulness
        orch.process_message("user", "Olá, eu amo as estrelas.")
        orch.process_message("being", "Estrelas? Me conte mais!")
        orch.process_message("user", "São sóis distantes, bilhões de anos.")
        orch.process_message(
            "user",
            "Você parece curiosa sobre o universo.",
            trait_deltas={
                "hexaco": {"inquisitiveness": 0.08},
                "schwartz": {"universalism_nature": 0.05},
                "tci_character": {"self_forgetfulness": 0.03},
            },
        )

        # 2. Learn a fact
        orch.learn_fact("Estrelas são sóis distantes.")

        # 3. Consolidate (twilight)
        archived = orch.consolidate()
        assert archived >= 0

        # 4. Sleep cycle
        result = orch.sleep(num_rollouts=50, svd_rank=4, seed=42)
        assert len(result.traits_before) == 72
        assert len(result.traits_after) == 72

        # 5. Verify personality evolution
        p = orch.personality
        assert p.development.interaction_count >= 1
        assert p.hexaco.inquisitiveness != 0.5  # Changed by trait delta + sleep

        # 6. Build prompt
        prompt = orch.build_prompt()
        assert "E2E-Being" in prompt
        assert 'language="pt"' in prompt
        assert "sensorimotor" in prompt


# ---------------------------------------------------------------------------
# Milestone-based Piaget progression
# ---------------------------------------------------------------------------


class TestLocalE2EMilestones:
    """Test milestone-based cognitive development through the full engine."""

    def test_milestone_advances_cognitive_age(self, mock_orchestrator: Orchestrator):
        """Recording a milestone advances cognitive_age proportionally."""
        engine = mock_orchestrator._personality_engine
        state = mock_orchestrator.personality

        state = engine.record_milestone(state, "object_permanence")
        assert state.development.cognitive_age > 0.0
        assert "object_permanence" in state.development.milestones_achieved

    def test_complete_stage_transitions_to_next(self, mock_orchestrator: Orchestrator):
        """Completing all sensorimotor milestones transitions to preoperational."""
        engine = mock_orchestrator._personality_engine
        state = mock_orchestrator.personality

        for milestone in STAGE_MILESTONES["sensorimotor"]:
            state = engine.record_milestone(state, milestone)

        assert state.development.stage == "preoperational"
        assert state.development.erikson_conflict == "autonomy_vs_shame"
        assert state.development.cognitive_age >= 24.0

    def test_full_piaget_progression(self, mock_orchestrator: Orchestrator):
        """Progress through all four Piaget stages via milestones."""
        engine = mock_orchestrator._personality_engine
        state = mock_orchestrator.personality

        for stage in STAGE_ORDER:
            for milestone in STAGE_MILESTONES[stage]:
                state = engine.record_milestone(state, milestone)

        assert state.development.stage == "formal_operational"
        assert state.development.erikson_conflict == "identity_vs_role_confusion"


# ---------------------------------------------------------------------------
# Event Sourcing
# ---------------------------------------------------------------------------


class TestLocalE2EEventSourcing:
    """Test Event Sourcing replay reproduces the correct state."""

    def test_event_store_replay_matches_direct_state(
        self, mock_orchestrator: Orchestrator
    ):
        """Events replayed produce the same state as direct mutations."""
        being_id = mock_orchestrator.being_id
        store = EventStore(ser_id=being_id)

        # Record creation
        store.record_being_created(name="ReplayBeing", language="pt")

        # Record trait updates
        store.record_trait_update({
            "hexaco": {"sincerity": 0.1, "liveliness": 0.05},
            "tci_character": {"empathy": 0.08},
        })

        # Record milestone
        store.record_milestone("object_permanence", new_cognitive_age=6.0)

        # Record belief
        store.record_belief("core", "The world is mostly safe.")

        # Replay and verify
        replayed = store.replay()
        assert replayed.name == "ReplayBeing"
        assert replayed.language == "pt"
        assert replayed.hexaco.sincerity == pytest.approx(0.6, abs=0.01)
        assert replayed.tci_character.empathy == pytest.approx(0.08, abs=0.01)
        assert replayed.development.cognitive_age == 6.0
        assert "The world is mostly safe." in replayed.core_beliefs

    def test_partial_replay(self, mock_orchestrator: Orchestrator):
        """Replaying up to a specific sequence number stops at that point."""
        store = EventStore(ser_id="partial-test")
        store.record_being_created(name="PartialBeing", language="en")
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})
        store.record_trait_update({"hexaco": {"sincerity": 0.1}})

        # Replay only up to sequence 2 (creation + first trait update)
        state = store.replay(up_to_sequence=2)
        assert state.hexaco.sincerity == pytest.approx(0.6, abs=0.01)

        # Full replay includes both updates
        full = store.replay()
        assert full.hexaco.sincerity == pytest.approx(0.7, abs=0.01)


# ---------------------------------------------------------------------------
# Protobuf round-trip
# ---------------------------------------------------------------------------


class TestLocalE2EProtoRoundTrip:
    """Test Protobuf serialization round-trip with a live personality."""

    def test_proto_roundtrip_preserves_evolved_state(
        self, mock_orchestrator: Orchestrator
    ):
        """An evolved personality survives Pydantic → Proto → Pydantic."""
        # Evolve the personality
        mock_orchestrator.process_message(
            "user",
            "Teste de serialização",
            trait_deltas={
                "hexaco": {"creativity": 0.12},
                "schwartz": {"stimulation": 0.07},
            },
        )

        original = mock_orchestrator.personality

        # Round-trip through protobuf
        ledger = personality_to_ledger(original)
        restored = ledger_to_personality(ledger)

        assert restored.being_id == original.being_id
        assert restored.name == original.name
        assert restored.language == original.language
        assert restored.hexaco.creativity == pytest.approx(
            original.hexaco.creativity, abs=0.01
        )
        assert restored.schwartz.stimulation == pytest.approx(
            original.schwartz.stimulation, abs=0.01
        )
        assert restored.development.stage == original.development.stage
        assert restored.development.interaction_count == original.development.interaction_count


# ---------------------------------------------------------------------------
# Prompt generation across languages
# ---------------------------------------------------------------------------


class TestLocalE2EPromptLanguages:
    """Test prompt generation across all supported languages."""

    LANGUAGES = ["en", "pt", "es", "fr"]

    @pytest.mark.parametrize("lang", LANGUAGES)
    def test_prompt_contains_language_tag(self, lang: str):
        """Each language produces a prompt with the correct language tag."""
        from unittest.mock import patch
        from tests.e2e.conftest import InMemoryArchival, InMemoryRelational

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
                being_name=f"Being-{lang}",
                language=lang,
            )
            prompt = orch.build_prompt()
            assert f'language="{lang}"' in prompt

    @pytest.mark.parametrize(
        "lang,keyword",
        [
            ("en", "TRUST"),
            ("pt", "CONFIANÇA"),
            ("es", "CONFIANZA"),
            ("fr", "CONFIANCE"),
        ],
    )
    def test_prompt_erikson_in_correct_language(self, lang: str, keyword: str):
        """Erikson conflict description appears in the correct language."""
        from unittest.mock import patch
        from tests.e2e.conftest import InMemoryArchival, InMemoryRelational

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
                being_name=f"Being-{lang}",
                language=lang,
            )
            prompt = orch.build_prompt()
            assert keyword in prompt
