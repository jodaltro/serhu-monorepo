"""Bidirectional conversion between Pydantic personality models and Protobuf messages.

Provides ``personality_to_ledger`` and ``ledger_to_personality`` for
converting between the Pydantic ``PersonalityState`` and the Protobuf
``PersonalityLedger`` used for binary serialization between services.
"""

from __future__ import annotations

from serhu_orchestrator.personality.types import (
    DevelopmentStage as PydanticDevelopmentStage,
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


# ---------------------------------------------------------------------------
# Pydantic → Protobuf
# ---------------------------------------------------------------------------


def _pydantic_to_score_map(
    model: HexacoFacets | TciTemperament | TciCharacter | SchwartzValues,
) -> dict[str, float]:
    """Extract field name → score mapping from a Pydantic model."""
    return {name: getattr(model, name) for name in type(model).model_fields}


def personality_to_ledger(state: PersonalityState) -> PersonalityLedger:
    """Convert a Pydantic ``PersonalityState`` to a Protobuf ``PersonalityLedger``.

    The ``cognitive_age_days`` convenience field is derived from
    ``development.cognitive_age`` (months → days, rounded down).
    """
    ledger = PersonalityLedger(
        ser_id=state.being_id,
        name=state.name,
        language=state.language,
        cognitive_age_days=int(state.development.cognitive_age * 30),
        piaget_stage=state.development.stage,
    )

    # Development stage
    ledger.development.CopyFrom(
        ProtoDevelopmentStage(
            stage=state.development.stage,
            erikson_conflict=state.development.erikson_conflict,
            cognitive_age=state.development.cognitive_age,
            interaction_count=state.development.interaction_count,
            milestones_achieved=state.development.milestones_achieved,
        )
    )

    # HEXACO – 24 facets
    for name, score in _pydantic_to_score_map(state.hexaco).items():
        ledger.hexaco[name].CopyFrom(HexacoFacet(score=score))

    # TCI-R Temperament – 16 subscales
    for name, score in _pydantic_to_score_map(state.tci_temperament).items():
        ledger.tci_temperament[name].CopyFrom(TciSubscale(score=score))

    # TCI-R Character – 13 subscales
    for name, score in _pydantic_to_score_map(state.tci_character).items():
        ledger.tci_character[name].CopyFrom(TciSubscale(score=score))

    # Schwartz – 19 values
    for name, score in _pydantic_to_score_map(state.schwartz).items():
        ledger.schwartz[name].CopyFrom(SchwartzValue(score=score))

    # Beliefs
    ledger.core_beliefs.extend(state.core_beliefs)
    ledger.surface_beliefs.extend(state.surface_beliefs)

    return ledger


# ---------------------------------------------------------------------------
# Protobuf → Pydantic
# ---------------------------------------------------------------------------


def _score_map_to_kwargs(
    proto_map: dict[str, HexacoFacet | TciSubscale | SchwartzValue],
) -> dict[str, float]:
    """Convert a Protobuf map<string, *Facet> to a dict of field → score."""
    return {name: msg.score for name, msg in proto_map.items()}


def ledger_to_personality(ledger: PersonalityLedger) -> PersonalityState:
    """Convert a Protobuf ``PersonalityLedger`` back to a Pydantic ``PersonalityState``."""
    dev = ledger.development
    development = PydanticDevelopmentStage(
        stage=dev.stage,
        erikson_conflict=dev.erikson_conflict,
        cognitive_age=dev.cognitive_age,
        interaction_count=dev.interaction_count,
        milestones_achieved=list(dev.milestones_achieved),
    )

    return PersonalityState(
        being_id=ledger.ser_id,
        name=ledger.name,
        language=ledger.language,
        development=development,
        hexaco=HexacoFacets(**_score_map_to_kwargs(ledger.hexaco)),
        tci_temperament=TciTemperament(**_score_map_to_kwargs(ledger.tci_temperament)),
        tci_character=TciCharacter(**_score_map_to_kwargs(ledger.tci_character)),
        schwartz=SchwartzValues(**_score_map_to_kwargs(ledger.schwartz)),
        core_beliefs=list(ledger.core_beliefs),
        surface_beliefs=list(ledger.surface_beliefs),
    )
