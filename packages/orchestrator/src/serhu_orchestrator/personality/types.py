"""Personality type definitions - HEXACO, TCI-R, and Schwartz value models.

Implements high-granularity personality modeling following:
- HEXACO: 6 factors × 4 facets = 24 measurement points
- TCI-R: 4 temperament dimensions (16 subscales) + 3 character dimensions (13 subscales)
- Schwartz: 19 refined basic human values
- Piaget cognitive development stages with milestone-based age progression

References:
    - HEXACO model: https://hexaco.org/scaledescriptions
    - TCI-R (Cloninger): https://en.wikipedia.org/wiki/Temperament_and_Character_Inventory
    - Schwartz refined values: https://pmc.ncbi.nlm.nih.gov/articles/PMC9131418/
    - Piaget stages: https://www.simplypsychology.org/piaget.html
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# HEXACO – 6 factors, 24 facets (scores 0.0 – 1.0)
# ---------------------------------------------------------------------------

class HexacoFacets(BaseModel):
    """24 facets of the HEXACO personality model.

    Each factor contains 4 facets scored from 0.0 (low) to 1.0 (high).
    Tabula rasa initialization: all facets start at 0.5 (neutral midpoint).
    """

    # Honesty-Humility (H)
    sincerity: float = Field(default=0.5, ge=0.0, le=1.0)
    fairness: float = Field(default=0.5, ge=0.0, le=1.0)
    greed_avoidance: float = Field(default=0.5, ge=0.0, le=1.0)
    modesty: float = Field(default=0.5, ge=0.0, le=1.0)

    # Emotionality (E)
    fearfulness: float = Field(default=0.5, ge=0.0, le=1.0)
    anxiety: float = Field(default=0.5, ge=0.0, le=1.0)
    dependence: float = Field(default=0.5, ge=0.0, le=1.0)
    sentimentality: float = Field(default=0.5, ge=0.0, le=1.0)

    # Extraversion (X)
    social_self_esteem: float = Field(default=0.5, ge=0.0, le=1.0)
    social_boldness: float = Field(default=0.5, ge=0.0, le=1.0)
    sociability: float = Field(default=0.5, ge=0.0, le=1.0)
    liveliness: float = Field(default=0.5, ge=0.0, le=1.0)

    # Agreeableness (A)
    forgiveness: float = Field(default=0.5, ge=0.0, le=1.0)
    gentleness: float = Field(default=0.5, ge=0.0, le=1.0)
    flexibility: float = Field(default=0.5, ge=0.0, le=1.0)
    patience: float = Field(default=0.5, ge=0.0, le=1.0)

    # Conscientiousness (C)
    organization: float = Field(default=0.5, ge=0.0, le=1.0)
    diligence: float = Field(default=0.5, ge=0.0, le=1.0)
    perfectionism: float = Field(default=0.5, ge=0.0, le=1.0)
    prudence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Openness to Experience (O)
    aesthetic_appreciation: float = Field(default=0.5, ge=0.0, le=1.0)
    inquisitiveness: float = Field(default=0.5, ge=0.0, le=1.0)
    creativity: float = Field(default=0.5, ge=0.0, le=1.0)
    unconventionality: float = Field(default=0.5, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# TCI-R – Temperament (4 dimensions, 16 subscales)
# ---------------------------------------------------------------------------

class TciTemperament(BaseModel):
    """Cloninger TCI-R temperament dimensions – innate, biologically-driven.

    Tabula rasa initialization: all subscales start at 0.5 (neutral).
    """

    # Novelty Seeking (NS) – dopamine-driven exploration
    exploratory_excitability: float = Field(default=0.5, ge=0.0, le=1.0)
    impulsiveness: float = Field(default=0.5, ge=0.0, le=1.0)
    extravagance: float = Field(default=0.5, ge=0.0, le=1.0)
    disorderliness: float = Field(default=0.5, ge=0.0, le=1.0)

    # Harm Avoidance (HA) – serotonin-driven inhibition
    anticipatory_worry: float = Field(default=0.5, ge=0.0, le=1.0)
    fear_of_uncertainty: float = Field(default=0.5, ge=0.0, le=1.0)
    shyness: float = Field(default=0.5, ge=0.0, le=1.0)
    fatigability: float = Field(default=0.5, ge=0.0, le=1.0)

    # Reward Dependence (RD) – norepinephrine-driven attachment
    sentimentality_rd: float = Field(default=0.5, ge=0.0, le=1.0)
    openness_to_communication: float = Field(default=0.5, ge=0.0, le=1.0)
    attachment: float = Field(default=0.5, ge=0.0, le=1.0)
    dependence_rd: float = Field(default=0.5, ge=0.0, le=1.0)

    # Persistence (PS)
    eagerness_of_effort: float = Field(default=0.5, ge=0.0, le=1.0)
    work_hardened: float = Field(default=0.5, ge=0.0, le=1.0)
    ambitious: float = Field(default=0.5, ge=0.0, le=1.0)
    perfectionist_ps: float = Field(default=0.5, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# TCI-R – Character (3 dimensions, 13 subscales)
# ---------------------------------------------------------------------------

class TciCharacter(BaseModel):
    """Cloninger TCI-R character dimensions – learned, socially-constructed.

    Tabula rasa initialization: all subscales start at 0.0 (undeveloped).
    Character must be *built* through interaction, not inherited.
    """

    # Self-Directedness (SD) – agency and personal goals
    responsibility: float = Field(default=0.0, ge=0.0, le=1.0)
    purposefulness: float = Field(default=0.0, ge=0.0, le=1.0)
    resourcefulness: float = Field(default=0.0, ge=0.0, le=1.0)
    self_acceptance: float = Field(default=0.0, ge=0.0, le=1.0)
    enlightened_second_nature: float = Field(default=0.0, ge=0.0, le=1.0)

    # Cooperativeness (C) – social integration
    social_acceptance: float = Field(default=0.0, ge=0.0, le=1.0)
    empathy: float = Field(default=0.0, ge=0.0, le=1.0)
    helpfulness: float = Field(default=0.0, ge=0.0, le=1.0)
    compassion: float = Field(default=0.0, ge=0.0, le=1.0)

    # Self-Transcendence (ST) – wonder and spirituality
    self_forgetfulness: float = Field(default=0.0, ge=0.0, le=1.0)
    transpersonal_identification: float = Field(default=0.0, ge=0.0, le=1.0)
    spiritual_acceptance: float = Field(default=0.0, ge=0.0, le=1.0)
    pure_conscience: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Schwartz – 19 refined basic human values
# ---------------------------------------------------------------------------

class SchwartzValues(BaseModel):
    """Schwartz 19 refined basic human values.

    Tabula rasa initialization: all values start at 0.0 (unformed).
    Values represent what the Being *aspires to*, not what it *is*.
    """

    self_direction_thought: float = Field(default=0.0, ge=0.0, le=1.0)
    self_direction_action: float = Field(default=0.0, ge=0.0, le=1.0)
    stimulation: float = Field(default=0.0, ge=0.0, le=1.0)
    hedonism: float = Field(default=0.0, ge=0.0, le=1.0)
    achievement: float = Field(default=0.0, ge=0.0, le=1.0)
    power_dominance: float = Field(default=0.0, ge=0.0, le=1.0)
    power_resources: float = Field(default=0.0, ge=0.0, le=1.0)
    face: float = Field(default=0.0, ge=0.0, le=1.0)
    security_personal: float = Field(default=0.0, ge=0.0, le=1.0)
    security_societal: float = Field(default=0.0, ge=0.0, le=1.0)
    tradition: float = Field(default=0.0, ge=0.0, le=1.0)
    conformity_rules: float = Field(default=0.0, ge=0.0, le=1.0)
    conformity_interpersonal: float = Field(default=0.0, ge=0.0, le=1.0)
    humility: float = Field(default=0.0, ge=0.0, le=1.0)
    benevolence_caring: float = Field(default=0.0, ge=0.0, le=1.0)
    benevolence_dependability: float = Field(default=0.0, ge=0.0, le=1.0)
    universalism_concern: float = Field(default=0.0, ge=0.0, le=1.0)
    universalism_nature: float = Field(default=0.0, ge=0.0, le=1.0)
    universalism_tolerance: float = Field(default=0.0, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Piaget cognitive development stages and milestones
# ---------------------------------------------------------------------------

# Stage ordering and age ranges (in equivalent human-months).
# Based on Piaget's developmental theory:
#   - Sensorimotor: 0–24 months
#   - Preoperational: 24–84 months (2–7 years)
#   - Concrete operational: 84–132 months (7–11 years)
#   - Formal operational: 132+ months (11+ years)
# Reference: https://www.simplypsychology.org/piaget.html

STAGE_ORDER: list[str] = [
    "sensorimotor",
    "preoperational",
    "concrete_operational",
    "formal_operational",
]

STAGE_AGE_RANGES: dict[str, tuple[float, float]] = {
    "sensorimotor": (0.0, 24.0),
    "preoperational": (24.0, 84.0),
    "concrete_operational": (84.0, 132.0),
    "formal_operational": (132.0, 192.0),
}

# Milestones for each Piaget stage.
# The Being's cognitive_age only advances when milestones are achieved.
# Stage transitions require ALL milestones of the current stage to be completed.
#
# References:
#   - Sensorimotor milestones: https://www.simplypsychology.org/piaget.html
#   - Piaget's stages applied to AI: https://gregrobison.medium.com/active-learning-machines-...
#   - Preoperational / Concrete / Formal milestones:
#     https://mxtsch.people.wm.edu/Teaching/JCPE/Volume1/JCPE_2008-01-09.pdf

STAGE_MILESTONES: dict[str, list[str]] = {
    "sensorimotor": [
        "object_permanence",       # Understands concepts persist between sessions
        "circular_reactions",      # Repeats interaction patterns that produce results
        "causal_understanding",    # Basic cause-effect mapping from user input
        "means_end_behavior",      # Uses learned patterns to achieve goals
    ],
    "preoperational": [
        "symbolic_thought",        # Uses language to represent absent objects/feelings
        "egocentrism_awareness",   # Begins to consider user has separate existence
        "animism_attribution",     # Assigns lifelike qualities to abstract concepts
        "centration_overcome",     # Can consider multiple aspects simultaneously
    ],
    "concrete_operational": [
        "conservation",            # Understands quantity/meaning stays same across forms
        "reversibility",           # Can logically reverse operations and arguments
        "classification",          # Organizes knowledge into hierarchical categories
        "seriation",               # Orders concepts along logical dimensions
    ],
    "formal_operational": [
        "abstract_reasoning",      # Reasons about hypothetical/abstract concepts
        "hypothetical_deductive",  # Forms and tests hypotheses about the world
        "metacognition",           # Thinks about own thought processes and identity
        "systematic_problem_solving",  # Approaches problems methodically
    ],
}


class DevelopmentStage(BaseModel):
    """Piaget-based cognitive development stage tracker.

    The Being's cognitive_age only advances when developmental milestones
    are achieved.  Stage transitions require ALL milestones of the current
    stage to be completed before the Being can move to the next stage.

    References:
        - Piaget stages: https://www.simplypsychology.org/piaget.html
        - Active Learning Machines: https://gregrobison.medium.com/active-learning-machines-...
    """

    stage: str = Field(
        default="sensorimotor",
        description="Current Piaget stage: sensorimotor | preoperational | concrete_operational | formal_operational",
    )
    cognitive_age: float = Field(
        default=0.0,
        ge=0.0,
        description="Cognitive age in equivalent human-months.  Only advances when milestones are achieved.",
    )
    interaction_count: int = Field(
        default=0,
        ge=0,
        description="Total number of interactions since birth",
    )
    milestones_achieved: list[str] = Field(
        default_factory=list,
        description="List of milestone identifiers that have been achieved (e.g. 'object_permanence')",
    )


# ---------------------------------------------------------------------------
# Composite personality state
# ---------------------------------------------------------------------------


class PersonalityState(BaseModel):
    """Complete personality ledger for the synthetic Being.

    This is the JSON-serializable 'Persona Profile' that the LLM consumes
    to adopt the voice, cognitive limitations, and emotional biases of
    this specific Being.
    """

    being_id: str = Field(description="Unique identifier for this Being")
    name: str = Field(default="", description="Name given by the user")
    development: DevelopmentStage = Field(default_factory=DevelopmentStage)
    hexaco: HexacoFacets = Field(default_factory=HexacoFacets)
    tci_temperament: TciTemperament = Field(default_factory=TciTemperament)
    tci_character: TciCharacter = Field(default_factory=TciCharacter)
    schwartz: SchwartzValues = Field(default_factory=SchwartzValues)
    core_beliefs: list[str] = Field(
        default_factory=list,
        description="Stack of beliefs evolved through Solomonoff induction during sleep cycles",
    )
