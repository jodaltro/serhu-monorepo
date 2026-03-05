"""Unit tests for Protobuf PersonalityLedger and Pydantic ↔ Protobuf conversion."""

import math

import pytest

from serhu_orchestrator.personality.types import (
    DevelopmentStage,
    HexacoFacets,
    PersonalityState,
    SchwartzValues,
    TciCharacter,
    TciTemperament,
)
from serhu_orchestrator.proto.ser_identity_pb2 import (
    DevelopmentStage as ProtoDevelopmentStage,
    HexacoFacet,
    PersonalityLedger,
    SchwartzValue,
    TciSubscale,
)
from serhu_orchestrator.personality.proto_converter import (
    ledger_to_personality,
    personality_to_ledger,
)


# ---------------------------------------------------------------------------
# Protobuf message construction
# ---------------------------------------------------------------------------


class TestProtobufMessages:
    """Basic tests for the generated Protobuf messages."""

    def test_hexaco_facet_default(self):
        facet = HexacoFacet()
        assert facet.score == 0.0  # proto3 default

    def test_hexaco_facet_with_score(self):
        facet = HexacoFacet(score=0.75)
        assert math.isclose(facet.score, 0.75, rel_tol=1e-5)

    def test_tci_subscale(self):
        sub = TciSubscale(score=0.5)
        assert math.isclose(sub.score, 0.5, rel_tol=1e-5)

    def test_schwartz_value(self):
        val = SchwartzValue(score=0.3)
        assert math.isclose(val.score, 0.3, rel_tol=1e-5)

    def test_development_stage(self):
        stage = ProtoDevelopmentStage(
            stage="sensorimotor",
            erikson_conflict="trust_vs_mistrust",
            cognitive_age=3.5,
            interaction_count=42,
            milestones_achieved=["object_permanence"],
        )
        assert stage.stage == "sensorimotor"
        assert stage.erikson_conflict == "trust_vs_mistrust"
        assert math.isclose(stage.cognitive_age, 3.5, rel_tol=1e-5)
        assert stage.interaction_count == 42
        assert list(stage.milestones_achieved) == ["object_permanence"]

    def test_personality_ledger_scalar_fields(self):
        ledger = PersonalityLedger(
            ser_id="being-001",
            cognitive_age_days=90,
            piaget_stage="sensorimotor",
            name="Luna",
            language="pt",
        )
        assert ledger.ser_id == "being-001"
        assert ledger.cognitive_age_days == 90
        assert ledger.piaget_stage == "sensorimotor"
        assert ledger.name == "Luna"
        assert ledger.language == "pt"

    def test_personality_ledger_hexaco_map(self):
        ledger = PersonalityLedger()
        ledger.hexaco["sincerity"].CopyFrom(HexacoFacet(score=0.8))
        ledger.hexaco["fairness"].CopyFrom(HexacoFacet(score=0.6))
        assert math.isclose(ledger.hexaco["sincerity"].score, 0.8, rel_tol=1e-5)
        assert math.isclose(ledger.hexaco["fairness"].score, 0.6, rel_tol=1e-5)
        assert len(ledger.hexaco) == 2

    def test_personality_ledger_beliefs(self):
        ledger = PersonalityLedger()
        ledger.core_beliefs.extend(["the world is safe", "learning is good"])
        ledger.surface_beliefs.append("dogs are friendly")
        assert list(ledger.core_beliefs) == ["the world is safe", "learning is good"]
        assert list(ledger.surface_beliefs) == ["dogs are friendly"]


# ---------------------------------------------------------------------------
# Binary serialization round-trip
# ---------------------------------------------------------------------------


class TestProtobufSerialization:
    """Verify that PersonalityLedger survives binary serialization."""

    def _make_ledger(self) -> PersonalityLedger:
        ledger = PersonalityLedger(
            ser_id="being-123",
            cognitive_age_days=60,
            piaget_stage="sensorimotor",
            name="Aria",
            language="en",
        )
        ledger.development.CopyFrom(
            ProtoDevelopmentStage(
                stage="sensorimotor",
                erikson_conflict="trust_vs_mistrust",
                cognitive_age=2.0,
                interaction_count=15,
                milestones_achieved=["object_permanence", "circular_reactions"],
            )
        )
        ledger.hexaco["sincerity"].CopyFrom(HexacoFacet(score=0.7))
        ledger.hexaco["anxiety"].CopyFrom(HexacoFacet(score=0.3))
        ledger.tci_temperament["exploratory_excitability"].CopyFrom(TciSubscale(score=0.6))
        ledger.tci_character["empathy"].CopyFrom(TciSubscale(score=0.1))
        ledger.schwartz["stimulation"].CopyFrom(SchwartzValue(score=0.4))
        ledger.core_beliefs.append("the user is kind")
        ledger.surface_beliefs.extend(["today was fun", "cats are soft"])
        return ledger

    def test_serialize_deserialize_roundtrip(self):
        original = self._make_ledger()
        data = original.SerializeToString()
        assert isinstance(data, bytes)
        assert len(data) > 0

        restored = PersonalityLedger()
        restored.ParseFromString(data)

        assert restored.ser_id == original.ser_id
        assert restored.name == original.name
        assert restored.language == original.language
        assert restored.cognitive_age_days == original.cognitive_age_days
        assert restored.piaget_stage == original.piaget_stage
        assert math.isclose(
            restored.hexaco["sincerity"].score,
            original.hexaco["sincerity"].score,
            rel_tol=1e-5,
        )
        assert math.isclose(
            restored.development.cognitive_age,
            original.development.cognitive_age,
            rel_tol=1e-5,
        )
        assert list(restored.development.milestones_achieved) == [
            "object_permanence",
            "circular_reactions",
        ]
        assert list(restored.core_beliefs) == ["the user is kind"]
        assert list(restored.surface_beliefs) == ["today was fun", "cats are soft"]

    def test_binary_is_compact(self):
        """Protobuf binary should be smaller than equivalent JSON."""
        ledger = self._make_ledger()
        binary_size = len(ledger.SerializeToString())
        # The binary representation should be non-trivially small
        assert binary_size < 500


# ---------------------------------------------------------------------------
# Pydantic ↔ Protobuf conversion
# ---------------------------------------------------------------------------


class TestPydanticToProtobuf:
    """Test conversion from PersonalityState to PersonalityLedger."""

    def _make_personality(self) -> PersonalityState:
        return PersonalityState(
            being_id="ser-42",
            name="Nova",
            language="pt",
            development=DevelopmentStage(
                stage="preoperational",
                erikson_conflict="autonomy_vs_shame",
                cognitive_age=30.0,
                interaction_count=200,
                milestones_achieved=[
                    "object_permanence",
                    "circular_reactions",
                    "causal_understanding",
                    "means_end_behavior",
                    "symbolic_thought",
                ],
            ),
            hexaco=HexacoFacets(sincerity=0.8, creativity=0.9),
            tci_temperament=TciTemperament(exploratory_excitability=0.7),
            tci_character=TciCharacter(empathy=0.3, compassion=0.2),
            schwartz=SchwartzValues(stimulation=0.6, hedonism=0.4),
            core_beliefs=["the world is beautiful"],
            surface_beliefs=["music is nice", "stars shine"],
        )

    def test_scalar_fields(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert ledger.ser_id == "ser-42"
        assert ledger.name == "Nova"
        assert ledger.language == "pt"
        assert ledger.piaget_stage == "preoperational"
        # cognitive_age 30.0 months * 30 = 900 days
        assert ledger.cognitive_age_days == 900

    def test_hexaco_map_has_24_entries(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert len(ledger.hexaco) == 24

    def test_hexaco_values_preserved(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert math.isclose(ledger.hexaco["sincerity"].score, 0.8, rel_tol=1e-5)
        assert math.isclose(ledger.hexaco["creativity"].score, 0.9, rel_tol=1e-5)
        # Default facets should be 0.5
        assert math.isclose(ledger.hexaco["fairness"].score, 0.5, rel_tol=1e-5)

    def test_tci_temperament_map_has_16_entries(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert len(ledger.tci_temperament) == 16

    def test_tci_character_map_has_13_entries(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert len(ledger.tci_character) == 13

    def test_schwartz_map_has_19_entries(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert len(ledger.schwartz) == 19

    def test_development_stage(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert ledger.development.stage == "preoperational"
        assert ledger.development.erikson_conflict == "autonomy_vs_shame"
        assert math.isclose(ledger.development.cognitive_age, 30.0, rel_tol=1e-5)
        assert ledger.development.interaction_count == 200
        assert "symbolic_thought" in ledger.development.milestones_achieved

    def test_beliefs(self):
        state = self._make_personality()
        ledger = personality_to_ledger(state)
        assert list(ledger.core_beliefs) == ["the world is beautiful"]
        assert list(ledger.surface_beliefs) == ["music is nice", "stars shine"]


class TestProtobufToPydantic:
    """Test conversion from PersonalityLedger back to PersonalityState."""

    def test_full_roundtrip(self):
        """PersonalityState → Ledger → binary → Ledger → PersonalityState."""
        original = PersonalityState(
            being_id="ser-round",
            name="Echo",
            language="es",
            development=DevelopmentStage(
                stage="concrete_operational",
                erikson_conflict="industry_vs_inferiority",
                cognitive_age=100.0,
                interaction_count=1500,
                milestones_achieved=["conservation", "reversibility"],
            ),
            hexaco=HexacoFacets(sincerity=0.9, patience=0.2),
            tci_temperament=TciTemperament(shyness=0.8),
            tci_character=TciCharacter(responsibility=0.7),
            schwartz=SchwartzValues(tradition=0.5),
            core_beliefs=["knowledge is power"],
            surface_beliefs=["rain is calming"],
        )

        # Pydantic → Proto → binary → Proto → Pydantic
        ledger = personality_to_ledger(original)
        binary = ledger.SerializeToString()

        restored_ledger = PersonalityLedger()
        restored_ledger.ParseFromString(binary)

        restored = ledger_to_personality(restored_ledger)

        assert restored.being_id == original.being_id
        assert restored.name == original.name
        assert restored.language == original.language
        assert restored.development.stage == original.development.stage
        assert restored.development.erikson_conflict == original.development.erikson_conflict
        assert math.isclose(
            restored.development.cognitive_age,
            original.development.cognitive_age,
            rel_tol=1e-5,
        )
        assert restored.development.interaction_count == original.development.interaction_count
        assert set(restored.development.milestones_achieved) == set(
            original.development.milestones_achieved
        )

        # Check HEXACO values survive the round-trip
        assert math.isclose(restored.hexaco.sincerity, 0.9, rel_tol=1e-3)
        assert math.isclose(restored.hexaco.patience, 0.2, rel_tol=1e-3)
        # Default facets
        assert math.isclose(restored.hexaco.fairness, 0.5, rel_tol=1e-3)

        # TCI
        assert math.isclose(restored.tci_temperament.shyness, 0.8, rel_tol=1e-3)
        assert math.isclose(restored.tci_character.responsibility, 0.7, rel_tol=1e-3)

        # Schwartz
        assert math.isclose(restored.schwartz.tradition, 0.5, rel_tol=1e-3)

        # Beliefs
        assert restored.core_beliefs == original.core_beliefs
        assert restored.surface_beliefs == original.surface_beliefs

    def test_tabula_rasa_roundtrip(self):
        """A fresh Being with all defaults should survive the round-trip."""
        original = PersonalityState(being_id="blank-slate")
        ledger = personality_to_ledger(original)
        restored = ledger_to_personality(ledger)

        assert restored.being_id == "blank-slate"
        assert restored.name == ""
        assert restored.language == "en"
        assert restored.development.stage == "sensorimotor"

        # HEXACO defaults (0.5)
        for field_name in HexacoFacets.model_fields:
            assert math.isclose(
                getattr(restored.hexaco, field_name), 0.5, rel_tol=1e-3
            ), f"HEXACO {field_name} should round-trip as 0.5"

        # TCI Temperament defaults (0.5)
        for field_name in TciTemperament.model_fields:
            assert math.isclose(
                getattr(restored.tci_temperament, field_name), 0.5, rel_tol=1e-3
            ), f"TCI-T {field_name} should round-trip as 0.5"

        # TCI Character defaults (0.0)
        for field_name in TciCharacter.model_fields:
            assert math.isclose(
                getattr(restored.tci_character, field_name), 0.0, abs_tol=1e-3
            ), f"TCI-C {field_name} should round-trip as 0.0"

        # Schwartz defaults (0.0)
        for field_name in SchwartzValues.model_fields:
            assert math.isclose(
                getattr(restored.schwartz, field_name), 0.0, abs_tol=1e-3
            ), f"Schwartz {field_name} should round-trip as 0.0"
