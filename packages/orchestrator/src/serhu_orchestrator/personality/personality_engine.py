"""Personality Engine – Tabula rasa initialization and trait evolution.

Manages the lifecycle of a Being's personality: creation as a blank slate,
incremental updates based on interaction analysis, and persistence through
the relational memory tier.

References:
    - Profile-LLM dynamic optimization: https://arxiv.org/html/2511.19852v1
    - HEXACO: https://hexaco.org/scaledescriptions
    - Piaget stages: https://www.simplypsychology.org/piaget.html
"""

from __future__ import annotations

import uuid

from serhu_orchestrator.personality.types import (
    DevelopmentStage,
    HexacoFacets,
    PersonalityState,
    SchwartzValues,
    TciCharacter,
    TciTemperament,
)
from serhu_orchestrator.memory.relational_memory import RelationalMemory


# Stage transition thresholds (interaction counts)
_STAGE_THRESHOLDS = {
    "sensorimotor": 0,
    "preoperational": 50,
    "concrete_operational": 200,
    "formal_operational": 500,
}

_STAGE_ORDER = [
    "sensorimotor",
    "preoperational",
    "concrete_operational",
    "formal_operational",
]


class PersonalityEngine:
    """Manages the Being's personality lifecycle.

    Parameters
    ----------
    relational : RelationalMemory
        Relational memory tier for personality persistence.
    """

    def __init__(self, relational: RelationalMemory) -> None:
        self.relational = relational

    # -- lifecycle -----------------------------------------------------------

    def create_being(self, name: str = "") -> PersonalityState:
        """Create a new Being as a *tabula rasa*.

        - HEXACO facets start at 0.5 (neutral midpoint)
        - TCI-R temperament starts at 0.5 (neutral)
        - TCI-R character starts at 0.0 (must be built)
        - Schwartz values start at 0.0 (unformed)
        - Development stage: sensorimotor, age 0

        Returns
        -------
        PersonalityState
            A fresh personality state ready for interaction.
        """
        being_id = uuid.uuid4().hex
        state = PersonalityState(
            being_id=being_id,
            name=name,
            development=DevelopmentStage(),
            hexaco=HexacoFacets(),
            tci_temperament=TciTemperament(),
            tci_character=TciCharacter(),
            schwartz=SchwartzValues(),
            core_beliefs=[],
        )
        self._persist(state)
        return state

    def load_being(self, being_id: str) -> PersonalityState | None:
        """Load a Being's personality from relational memory.

        Returns
        -------
        PersonalityState | None
            The loaded state, or ``None`` if the Being does not exist.
        """
        data = self.relational.load_personality(being_id)
        if data is None:
            return None
        return PersonalityState(**data)

    # -- trait update --------------------------------------------------------

    def update_traits(
        self,
        state: PersonalityState,
        deltas: dict[str, dict[str, float]],
    ) -> PersonalityState:
        """Apply incremental trait updates and advance development.

        Parameters
        ----------
        state : PersonalityState
            Current personality state.
        deltas : dict[str, dict[str, float]]
            Nested dict mapping model name to facet-name → delta.
            Example::

                {
                    "hexaco": {"sincerity": 0.02, "liveliness": -0.01},
                    "tci_character": {"empathy": 0.03},
                }

        Returns
        -------
        PersonalityState
            Updated personality state (persisted automatically).
        """
        model_map = {
            "hexaco": state.hexaco,
            "tci_temperament": state.tci_temperament,
            "tci_character": state.tci_character,
            "schwartz": state.schwartz,
        }

        for model_name, facet_deltas in deltas.items():
            model = model_map.get(model_name)
            if model is None:
                continue
            for facet_name, delta in facet_deltas.items():
                if hasattr(model, facet_name):
                    current = getattr(model, facet_name)
                    new_val = max(0.0, min(1.0, current + delta))
                    setattr(model, facet_name, new_val)

        # Advance development
        state.development.interaction_count += 1
        state.development.cognitive_age += 0.1  # ~1 month per 10 interactions
        state = self._check_stage_transition(state)

        self._persist(state)
        return state

    # -- internal ------------------------------------------------------------

    def _check_stage_transition(self, state: PersonalityState) -> PersonalityState:
        """Check if the Being should advance to the next Piaget stage."""
        count = state.development.interaction_count
        current_idx = _STAGE_ORDER.index(state.development.stage)

        for i in range(len(_STAGE_ORDER) - 1, -1, -1):
            stage_name = _STAGE_ORDER[i]
            if count >= _STAGE_THRESHOLDS[stage_name] and i > current_idx:
                state.development.stage = stage_name
                break

        return state

    def _persist(self, state: PersonalityState) -> None:
        """Save the personality state to relational memory."""
        self.relational.save_personality(
            being_id=state.being_id,
            state_json=state.model_dump(),
        )
