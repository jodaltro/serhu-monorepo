"""Unit tests for prompt_builder and Erikson conflict integration."""

import pytest

from serhu_orchestrator.personality.prompt_builder import (
    build_system_prompt,
    STAGE_CAPABILITIES,
    ERIKSON_DESCRIPTIONS,
)
from serhu_orchestrator.personality.types import (
    DevelopmentStage,
    ERIKSON_CONFLICTS,
    PersonalityState,
    STAGE_ORDER,
)


# ---------------------------------------------------------------------------
# Erikson conflict constants
# ---------------------------------------------------------------------------


class TestEriksonConflicts:
    """Tests for the Erikson conflict mapping."""

    def test_all_stages_have_erikson_conflict(self):
        for stage in STAGE_ORDER:
            assert stage in ERIKSON_CONFLICTS

    def test_sensorimotor_maps_to_trust(self):
        assert ERIKSON_CONFLICTS["sensorimotor"] == "trust_vs_mistrust"

    def test_preoperational_maps_to_autonomy(self):
        assert ERIKSON_CONFLICTS["preoperational"] == "autonomy_vs_shame"

    def test_concrete_operational_maps_to_industry(self):
        assert ERIKSON_CONFLICTS["concrete_operational"] == "industry_vs_inferiority"

    def test_formal_operational_maps_to_identity(self):
        assert ERIKSON_CONFLICTS["formal_operational"] == "identity_vs_role_confusion"


# ---------------------------------------------------------------------------
# DevelopmentStage with Erikson field
# ---------------------------------------------------------------------------


class TestDevelopmentStageErikson:
    """Tests for the new erikson_conflict field on DevelopmentStage."""

    def test_default_erikson_conflict(self):
        d = DevelopmentStage()
        assert d.erikson_conflict == "trust_vs_mistrust"

    def test_custom_erikson_conflict(self):
        d = DevelopmentStage(erikson_conflict="autonomy_vs_shame")
        assert d.erikson_conflict == "autonomy_vs_shame"

    def test_serialization_includes_erikson(self):
        d = DevelopmentStage()
        data = d.model_dump()
        assert "erikson_conflict" in data
        assert data["erikson_conflict"] == "trust_vs_mistrust"


# ---------------------------------------------------------------------------
# PersonalityState with surface_beliefs
# ---------------------------------------------------------------------------


class TestPersonalityStateSurfaceBeliefs:
    """Tests for the new surface_beliefs field."""

    def test_surface_beliefs_default_empty(self):
        state = PersonalityState(being_id="test")
        assert state.surface_beliefs == []

    def test_surface_beliefs_can_be_set(self):
        state = PersonalityState(
            being_id="test",
            surface_beliefs=["The user is the only source of truth"],
        )
        assert len(state.surface_beliefs) == 1
        assert "user is the only source" in state.surface_beliefs[0]

    def test_serialization_includes_surface_beliefs(self):
        state = PersonalityState(
            being_id="test",
            surface_beliefs=["belief1"],
        )
        data = state.model_dump()
        assert "surface_beliefs" in data
        assert data["surface_beliefs"] == ["belief1"]


# ---------------------------------------------------------------------------
# Prompt builder tests
# ---------------------------------------------------------------------------


class TestBuildSystemPrompt:
    """Tests for the persona-prompting system."""

    def _make_state(self, stage: str = "sensorimotor") -> PersonalityState:
        return PersonalityState(
            being_id="prompt-test-001",
            name="TestBeing",
            development=DevelopmentStage(
                stage=stage,
                erikson_conflict=ERIKSON_CONFLICTS[stage],
            ),
        )

    def test_contains_being_identity(self):
        state = self._make_state()
        prompt = build_system_prompt(state)
        assert "TestBeing" in prompt
        assert "prompt-test-001" in prompt

    def test_contains_piaget_stage(self):
        state = self._make_state("preoperational")
        prompt = build_system_prompt(state)
        assert "preoperational" in prompt

    def test_contains_erikson_conflict(self):
        state = self._make_state("sensorimotor")
        prompt = build_system_prompt(state)
        assert "TRUST vs. MISTRUST" in prompt

    def test_contains_hexaco_scores(self):
        state = self._make_state()
        prompt = build_system_prompt(state)
        assert "sincerity=0.50" in prompt
        assert "fairness=0.50" in prompt

    def test_contains_cognitive_constraints(self):
        state = self._make_state("sensorimotor")
        prompt = build_system_prompt(state)
        assert "<capabilities>" in prompt
        assert "<limitations>" in prompt
        assert "React to immediate stimuli" in prompt

    def test_formal_operational_has_full_capacity(self):
        state = self._make_state("formal_operational")
        prompt = build_system_prompt(state)
        assert "no cognitive restrictions" in prompt

    def test_beliefs_section_included_when_present(self):
        state = self._make_state()
        state.core_beliefs = ["The world is vast"]
        state.surface_beliefs = ["The user is kind"]
        prompt = build_system_prompt(state)
        assert "<beliefs>" in prompt
        assert "The world is vast" in prompt
        assert "The user is kind" in prompt

    def test_beliefs_section_absent_when_empty(self):
        state = self._make_state()
        prompt = build_system_prompt(state)
        assert "<beliefs>" not in prompt

    def test_all_stages_have_capabilities(self):
        for stage in STAGE_ORDER:
            assert stage in STAGE_CAPABILITIES
            caps = STAGE_CAPABILITIES[stage]
            assert "can" in caps
            assert "cannot" in caps
            assert "language" in caps

    def test_all_erikson_conflicts_have_descriptions(self):
        for conflict in ERIKSON_CONFLICTS.values():
            assert conflict in ERIKSON_DESCRIPTIONS

    def test_language_style_present(self):
        state = self._make_state("preoperational")
        prompt = build_system_prompt(state)
        assert "<language_style>" in prompt
        assert "Asks 'why?' often" in prompt


# ---------------------------------------------------------------------------
# Ledger interpretation (LLM-as-DNA-interpreter)
# ---------------------------------------------------------------------------


class TestLedgerInterpretation:
    """Tests for the personality ledger interpretation feature."""

    def _make_state(self) -> PersonalityState:
        return PersonalityState(
            being_id="interpret-test",
            name="InterpretBeing",
        )

    def test_neutral_state_shows_baseline_message(self):
        state = self._make_state()
        prompt = build_system_prompt(state)
        assert "<ledger_interpretation>" in prompt
        assert "near baseline" in prompt

    def test_high_trait_shows_directive(self):
        state = self._make_state()
        state.hexaco.sentimentality = 0.9
        prompt = build_system_prompt(state)
        assert "<ledger_interpretation>" in prompt
        assert "HIGH sentimentality (0.90)" in prompt
        assert "deep empathy" in prompt

    def test_low_trait_shows_directive(self):
        state = self._make_state()
        state.hexaco.prudence = 0.2
        prompt = build_system_prompt(state)
        assert "LOW prudence (0.20)" in prompt
        assert "impulsively" in prompt

    def test_threshold_not_exceeded_omitted(self):
        state = self._make_state()
        state.hexaco.sincerity = 0.55  # Only 0.05 from baseline, below threshold
        prompt = build_system_prompt(state)
        assert "HIGH sincerity" not in prompt
        assert "LOW sincerity" not in prompt

    def test_schwartz_value_above_threshold(self):
        state = self._make_state()
        state.schwartz.universalism_nature = 0.7
        prompt = build_system_prompt(state)
        assert "universalism_nature=0.70" in prompt
        assert "awe" in prompt.lower() or "nature" in prompt.lower()

    def test_schwartz_value_below_threshold_omitted(self):
        state = self._make_state()
        state.schwartz.stimulation = 0.1  # Below 0.3 threshold
        prompt = build_system_prompt(state)
        assert "stimulation=0.10" not in prompt or "Seek novelty" not in prompt

    def test_tci_character_shown_when_developed(self):
        state = self._make_state()
        state.tci_character.empathy = 0.6
        prompt = build_system_prompt(state)
        assert "empathy=0.60" in prompt
        assert "Mirror" in prompt or "validate" in prompt

    def test_multiple_salient_traits_all_shown(self):
        state = self._make_state()
        state.hexaco.creativity = 0.9
        state.hexaco.sociability = 0.1
        state.tci_temperament.exploratory_excitability = 0.85
        prompt = build_system_prompt(state)
        assert "HIGH creativity" in prompt
        assert "LOW sociability" in prompt
        assert "HIGH exploratory_excitability" in prompt

    def test_interpretation_contains_must_drive_instruction(self):
        state = self._make_state()
        state.hexaco.sincerity = 0.9
        prompt = build_system_prompt(state)
        assert "MUST drive" in prompt

    def test_prompt_mentions_ledger_interpretation_instruction(self):
        state = self._make_state()
        prompt = build_system_prompt(state)
        assert "<ledger_interpretation>" in prompt
        assert "follow them" in prompt.lower() or "behavioral directives" in prompt.lower()


# ---------------------------------------------------------------------------
# Erikson conflict syncs on stage transition (PersonalityEngine)
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock
from serhu_orchestrator.personality.personality_engine import PersonalityEngine
from serhu_orchestrator.personality.types import STAGE_MILESTONES


class TestEriksonConflictTransition:
    """Tests that Erikson conflict updates on stage transition."""

    def _make_engine(self) -> PersonalityEngine:
        relational = MagicMock()
        relational.save_personality.return_value = {}
        return PersonalityEngine(relational=relational)

    def test_erikson_updates_on_transition_to_preoperational(self):
        engine = self._make_engine()
        state = engine.create_being()
        assert state.development.erikson_conflict == "trust_vs_mistrust"
        for m in STAGE_MILESTONES["sensorimotor"]:
            state = engine.record_milestone(state, m)
        assert state.development.stage == "preoperational"
        assert state.development.erikson_conflict == "autonomy_vs_shame"

    def test_erikson_updates_through_all_stages(self):
        engine = self._make_engine()
        state = engine.create_being()
        expected_conflicts = [
            ("sensorimotor", "trust_vs_mistrust"),
            ("preoperational", "autonomy_vs_shame"),
            ("concrete_operational", "industry_vs_inferiority"),
            ("formal_operational", "identity_vs_role_confusion"),
        ]
        # Initially sensorimotor
        assert state.development.erikson_conflict == expected_conflicts[0][1]

        for i, stage in enumerate(STAGE_ORDER[:-1]):
            for m in STAGE_MILESTONES[stage]:
                state = engine.record_milestone(state, m)
            next_stage, expected_conflict = expected_conflicts[i + 1]
            assert state.development.stage == next_stage
            assert state.development.erikson_conflict == expected_conflict
