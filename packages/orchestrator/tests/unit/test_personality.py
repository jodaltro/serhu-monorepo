"""Unit tests for PersonalityState types and PersonalityEngine."""

import pytest

from serhu_orchestrator.personality.types import (
    DevelopmentStage,
    HexacoFacets,
    PersonalityState,
    SchwartzValues,
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


class TestPersonalityState:
    """Tests for the composite PersonalityState model."""

    def test_tabula_rasa_creation(self):
        state = PersonalityState(being_id="test-001")
        assert state.being_id == "test-001"
        assert state.name == ""
        assert state.development.stage == "sensorimotor"
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
