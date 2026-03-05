"""Unit tests for PersonalityState types and PersonalityEngine."""

import pytest

from serhu_orchestrator.personality.types import (
    DevelopmentStage,
    HexacoFacets,
    PersonalityState,
    SchwartzValues,
    STAGE_AGE_RANGES,
    STAGE_MILESTONES,
    STAGE_ORDER,
    TciCharacter,
    TciTemperament,
)


class TestHexacoFacets:
    """Tests for HEXACO personality model defaults and constraints."""

    def test_default_values_are_neutral(self):
        h = HexacoFacets()
        for field_name in HexacoFacets.model_fields:
            assert getattr(h, field_name) == 0.5, f"{field_name} should default to 0.5"

    def test_has_24_facets(self):
        assert len(HexacoFacets.model_fields) == 24

    def test_value_bounds(self):
        with pytest.raises(Exception):
            HexacoFacets(sincerity=1.5)
        with pytest.raises(Exception):
            HexacoFacets(sincerity=-0.1)


class TestTciTemperament:
    """Tests for TCI-R temperament defaults."""

    def test_default_values_are_neutral(self):
        t = TciTemperament()
        for field_name in TciTemperament.model_fields:
            assert getattr(t, field_name) == 0.5, f"{field_name} should default to 0.5"

    def test_has_16_subscales(self):
        assert len(TciTemperament.model_fields) == 16


class TestTciCharacter:
    """Tests for TCI-R character defaults (must be built, not inherited)."""

    def test_default_values_are_zero(self):
        c = TciCharacter()
        for field_name in TciCharacter.model_fields:
            assert getattr(c, field_name) == 0.0, f"{field_name} should default to 0.0"

    def test_has_13_subscales(self):
        assert len(TciCharacter.model_fields) == 13


class TestSchwartzValues:
    """Tests for Schwartz 19 refined values defaults."""

    def test_default_values_are_zero(self):
        s = SchwartzValues()
        for field_name in SchwartzValues.model_fields:
            assert getattr(s, field_name) == 0.0, f"{field_name} should default to 0.0"

    def test_has_19_values(self):
        assert len(SchwartzValues.model_fields) == 19


class TestDevelopmentStage:
    """Tests for Piaget-based development tracker."""

    def test_defaults(self):
        d = DevelopmentStage()
        assert d.stage == "sensorimotor"
        assert d.cognitive_age == 0.0
        assert d.interaction_count == 0
        assert d.milestones_achieved == []

    def test_milestones_achieved_persists(self):
        d = DevelopmentStage(milestones_achieved=["object_permanence"])
        assert "object_permanence" in d.milestones_achieved


class TestStageMilestonesDefinitions:
    """Tests for Piaget stage milestone definitions."""

    def test_all_stages_have_milestones(self):
        for stage in STAGE_ORDER:
            assert stage in STAGE_MILESTONES
            assert len(STAGE_MILESTONES[stage]) > 0

    def test_all_stages_have_age_ranges(self):
        for stage in STAGE_ORDER:
            assert stage in STAGE_AGE_RANGES
            start, end = STAGE_AGE_RANGES[stage]
            assert start < end

    def test_stage_order_has_four_stages(self):
        assert len(STAGE_ORDER) == 4

    def test_sensorimotor_milestones(self):
        milestones = STAGE_MILESTONES["sensorimotor"]
        assert "object_permanence" in milestones
        assert "circular_reactions" in milestones
        assert "causal_understanding" in milestones
        assert "means_end_behavior" in milestones

    def test_preoperational_milestones(self):
        milestones = STAGE_MILESTONES["preoperational"]
        assert "symbolic_thought" in milestones
        assert "egocentrism_awareness" in milestones

    def test_concrete_operational_milestones(self):
        milestones = STAGE_MILESTONES["concrete_operational"]
        assert "conservation" in milestones
        assert "reversibility" in milestones

    def test_formal_operational_milestones(self):
        milestones = STAGE_MILESTONES["formal_operational"]
        assert "abstract_reasoning" in milestones
        assert "metacognition" in milestones

    def test_no_duplicate_milestones_across_stages(self):
        all_milestones: list[str] = []
        for milestones in STAGE_MILESTONES.values():
            all_milestones.extend(milestones)
        assert len(all_milestones) == len(set(all_milestones))

    def test_age_ranges_are_contiguous(self):
        for i in range(len(STAGE_ORDER) - 1):
            _, end = STAGE_AGE_RANGES[STAGE_ORDER[i]]
            start, _ = STAGE_AGE_RANGES[STAGE_ORDER[i + 1]]
            assert end == start


class TestPersonalityState:
    """Tests for the composite PersonalityState model."""

    def test_tabula_rasa_creation(self):
        state = PersonalityState(being_id="test-001")
        assert state.being_id == "test-001"
        assert state.name == ""
        assert state.development.stage == "sensorimotor"
        assert state.development.milestones_achieved == []
        assert state.hexaco.sincerity == 0.5
        assert state.tci_character.empathy == 0.0
        assert state.schwartz.stimulation == 0.0
        assert state.core_beliefs == []

    def test_serialization_roundtrip(self):
        state = PersonalityState(being_id="test-002", name="Aurora")
        data = state.model_dump()
        restored = PersonalityState(**data)
        assert restored.being_id == "test-002"
        assert restored.name == "Aurora"
        assert restored.hexaco.sincerity == state.hexaco.sincerity
        assert restored.tci_character.empathy == state.tci_character.empathy

    def test_json_serialization(self):
        state = PersonalityState(being_id="test-003")
        json_str = state.model_dump_json()
        assert "test-003" in json_str
        assert "sensorimotor" in json_str

    def test_serialization_roundtrip_with_milestones(self):
        state = PersonalityState(
            being_id="test-004",
            development=DevelopmentStage(
                stage="sensorimotor",
                cognitive_age=6.0,
                interaction_count=10,
                milestones_achieved=["object_permanence"],
            ),
        )
        data = state.model_dump()
        restored = PersonalityState(**data)
        assert restored.development.milestones_achieved == ["object_permanence"]
        assert restored.development.cognitive_age == 6.0


# ---------------------------------------------------------------------------
# PersonalityEngine unit tests (milestone-based progression)
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock

from serhu_orchestrator.personality.personality_engine import PersonalityEngine


def _make_engine() -> PersonalityEngine:
    """Create a PersonalityEngine with a mocked RelationalMemory."""
    relational = MagicMock()
    relational.save_personality.return_value = {}
    relational.load_personality.return_value = None
    return PersonalityEngine(relational=relational)


class TestPersonalityEngineCreateBeing:
    """Tests for Being creation."""

    def test_new_being_starts_sensorimotor(self):
        engine = _make_engine()
        state = engine.create_being("Test")
        assert state.development.stage == "sensorimotor"
        assert state.development.cognitive_age == 0.0
        assert state.development.milestones_achieved == []
        assert state.development.interaction_count == 0


class TestPersonalityEngineUpdateTraits:
    """Tests that update_traits no longer auto-advances cognitive_age."""

    def test_interaction_count_increments(self):
        engine = _make_engine()
        state = engine.create_being()
        state = engine.update_traits(state, {"hexaco": {"sincerity": 0.01}})
        assert state.development.interaction_count == 1

    def test_cognitive_age_does_not_auto_advance(self):
        engine = _make_engine()
        state = engine.create_being()
        state = engine.update_traits(state, {"hexaco": {"sincerity": 0.01}})
        assert state.development.cognitive_age == 0.0

    def test_stage_does_not_change_without_milestones(self):
        engine = _make_engine()
        state = engine.create_being()
        for _ in range(100):
            state = engine.update_traits(state, {"hexaco": {"sincerity": 0.001}})
        assert state.development.stage == "sensorimotor"
        assert state.development.cognitive_age == 0.0


class TestPersonalityEngineRecordMilestone:
    """Tests for milestone-based age and stage advancement."""

    def test_record_single_milestone_advances_age(self):
        engine = _make_engine()
        state = engine.create_being()
        state = engine.record_milestone(state, "object_permanence")
        assert "object_permanence" in state.development.milestones_achieved
        # sensorimotor has 4 milestones over 24 months → 6.0 per milestone
        assert state.development.cognitive_age == pytest.approx(6.0)

    def test_duplicate_milestone_is_ignored(self):
        engine = _make_engine()
        state = engine.create_being()
        state = engine.record_milestone(state, "object_permanence")
        age_after_first = state.development.cognitive_age
        state = engine.record_milestone(state, "object_permanence")
        assert state.development.cognitive_age == age_after_first
        assert state.development.milestones_achieved.count("object_permanence") == 1

    def test_invalid_milestone_is_rejected(self):
        engine = _make_engine()
        state = engine.create_being()
        # "symbolic_thought" belongs to preoperational, not sensorimotor
        state = engine.record_milestone(state, "symbolic_thought")
        assert state.development.milestones_achieved == []
        assert state.development.cognitive_age == 0.0

    def test_nonexistent_milestone_is_rejected(self):
        engine = _make_engine()
        state = engine.create_being()
        state = engine.record_milestone(state, "does_not_exist")
        assert state.development.milestones_achieved == []

    def test_all_sensorimotor_milestones_triggers_stage_transition(self):
        engine = _make_engine()
        state = engine.create_being()
        milestones = [
            "object_permanence",
            "circular_reactions",
            "causal_understanding",
            "means_end_behavior",
        ]
        for m in milestones:
            state = engine.record_milestone(state, m)
        assert state.development.stage == "preoperational"
        assert state.development.cognitive_age >= 24.0

    def test_partial_milestones_do_not_trigger_transition(self):
        engine = _make_engine()
        state = engine.create_being()
        state = engine.record_milestone(state, "object_permanence")
        state = engine.record_milestone(state, "circular_reactions")
        assert state.development.stage == "sensorimotor"
        assert state.development.cognitive_age == pytest.approx(12.0)

    def test_full_lifecycle_sensorimotor_to_preoperational(self):
        engine = _make_engine()
        state = engine.create_being()
        # Complete sensorimotor
        for m in STAGE_MILESTONES["sensorimotor"]:
            state = engine.record_milestone(state, m)
        assert state.development.stage == "preoperational"
        # Now add preoperational milestone
        state = engine.record_milestone(state, "symbolic_thought")
        assert "symbolic_thought" in state.development.milestones_achieved
        # Age should advance within the preoperational range (24–84)
        expected_increment = (84.0 - 24.0) / 4  # 15.0
        assert state.development.cognitive_age == pytest.approx(24.0 + expected_increment)

    def test_full_lifecycle_through_all_stages(self):
        engine = _make_engine()
        state = engine.create_being()
        for stage in STAGE_ORDER:
            for m in STAGE_MILESTONES[stage]:
                state = engine.record_milestone(state, m)
        assert state.development.stage == "formal_operational"
        # All milestones achieved across all stages
        total_milestones = sum(len(v) for v in STAGE_MILESTONES.values())
        assert len(state.development.milestones_achieved) == total_milestones

    def test_age_snaps_to_next_stage_start_on_transition(self):
        engine = _make_engine()
        state = engine.create_being()
        for m in STAGE_MILESTONES["sensorimotor"]:
            state = engine.record_milestone(state, m)
        # Age should be at least 24.0 (start of preoperational)
        assert state.development.cognitive_age >= 24.0
        assert state.development.stage == "preoperational"
