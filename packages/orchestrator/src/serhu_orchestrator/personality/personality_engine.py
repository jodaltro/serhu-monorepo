"""Personality Engine – Tabula rasa initialization and trait evolution.

Manages the lifecycle of a Being's personality: creation as a blank slate,
incremental updates based on interaction analysis, milestone-based cognitive
age advancement, and persistence through the relational memory tier.

References:
    - Profile-LLM dynamic optimization: https://arxiv.org/html/2511.19852v1
    - HEXACO: https://hexaco.org/scaledescriptions
    - Piaget stages: https://www.simplypsychology.org/piaget.html
"""

from __future__ import annotations

import logging
import uuid

from serhu_orchestrator.personality.types import (
    DevelopmentStage,
    ERIKSON_CONFLICTS,
    HexacoFacets,
    PersonalityState,
    SchwartzValues,
    STAGE_AGE_RANGES,
    STAGE_MILESTONES,
    STAGE_ORDER,
    TciCharacter,
    TciTemperament,
)
from serhu_orchestrator.memory.relational_memory import RelationalMemory

logger = logging.getLogger(__name__)


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

    def create_being(self, name: str = "", language: str = "en") -> PersonalityState:
        """Create a new Being as a *tabula rasa*.

        - HEXACO facets start at 0.5 (neutral midpoint)
        - TCI-R temperament starts at 0.5 (neutral)
        - TCI-R character starts at 0.0 (must be built)
        - Schwartz values start at 0.0 (unformed)
        - Development stage: sensorimotor, age 0, no milestones

        Parameters
        ----------
        name : str
            Name for the new Being.
        language : str
            Default language code (e.g., 'en', 'pt', 'es', 'fr').

        Returns
        -------
        PersonalityState
            A fresh personality state ready for interaction.
        """
        being_id = uuid.uuid4().hex
        logger.info(f"✨ create_being: tabula rasa ~ id={being_id}, name={name!r}, lang={language}")
        state = PersonalityState(
            being_id=being_id,
            name=name,
            language=language,
            development=DevelopmentStage(),
            hexaco=HexacoFacets(),
            tci_temperament=TciTemperament(),
            tci_character=TciCharacter(),
            schwartz=SchwartzValues(),
            core_beliefs=[],
        )
        self._persist(state)
        logger.info(f"  → Personality persisted to relational memory")
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
        logger.info(f"📊 update_traits: applying {sum(len(v) for v in deltas.values())} facet deltas")
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
                    logger.info(f"  → {model_name}.{facet_name}: {current:.2f} → {new_val:.2f} (delta={delta:+.3f})")

        # Advance interaction count (age does NOT advance here)
        state.development.interaction_count += 1

        self._persist(state)
        logger.info(f"  ✓ Personality updated (interactions={state.development.interaction_count})")
        return state

    # -- milestone tracking --------------------------------------------------

    def record_milestone(
        self,
        state: PersonalityState,
        milestone_id: str,
    ) -> PersonalityState:
        """Record the achievement of a developmental milestone.

        The cognitive_age only advances when milestones are achieved.
        Each achieved milestone advances the age by a fraction proportional
        to the current stage's age span divided by its total milestones.

        When ALL milestones for the current stage are complete the Being
        transitions to the next Piaget stage.

        Parameters
        ----------
        state : PersonalityState
            Current personality state.
        milestone_id : str
            Identifier of the achieved milestone (must belong to the current
            stage or a previous stage).

        Returns
        -------
        PersonalityState
            Updated personality state (persisted automatically).
        """
        if milestone_id in state.development.milestones_achieved:
            return state  # already recorded

        current_stage = state.development.stage
        current_milestones = STAGE_MILESTONES.get(current_stage, [])

        # Only accept milestones that belong to the current stage
        if milestone_id not in current_milestones:
            return state

        state.development.milestones_achieved.append(milestone_id)

        # Advance cognitive age proportionally within the stage's age range
        age_start, age_end = STAGE_AGE_RANGES[current_stage]
        age_increment = (age_end - age_start) / max(len(current_milestones), 1)
        state.development.cognitive_age += age_increment

        # Check if all milestones for the current stage are complete
        state = self._check_stage_transition(state)

        self._persist(state)
        return state

    # -- internal ------------------------------------------------------------

    def _check_stage_transition(self, state: PersonalityState) -> PersonalityState:
        """Check if the Being should advance to the next Piaget stage.

        Stage advancement requires ALL milestones of the current stage
        to be achieved.  This follows Piaget's theory that cognitive
        stages are sequential and each builds upon the previous one.

        On transition, the Erikson psychosocial conflict is also updated
        to match the new stage (Reference: Erikson 8 stages).
        """
        current_stage = state.development.stage
        current_idx = STAGE_ORDER.index(current_stage)

        # Already at the final stage
        if current_idx >= len(STAGE_ORDER) - 1:
            return state

        required = set(STAGE_MILESTONES.get(current_stage, []))
        achieved = set(state.development.milestones_achieved)

        if required and required.issubset(achieved):
            next_stage = STAGE_ORDER[current_idx + 1]
            state.development.stage = next_stage
            state.development.erikson_conflict = ERIKSON_CONFLICTS[next_stage]
            # Snap age to the start of the new stage
            new_start, _ = STAGE_AGE_RANGES[next_stage]
            if state.development.cognitive_age < new_start:
                state.development.cognitive_age = new_start

        return state

    def _persist(self, state: PersonalityState) -> None:
        """Save the personality state to relational memory."""
        self.relational.save_personality(
            being_id=state.being_id,
            state_json=state.model_dump(),
        )
