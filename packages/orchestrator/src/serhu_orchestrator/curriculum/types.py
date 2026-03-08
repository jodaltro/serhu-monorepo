"""Pydantic models for the curriculum subsystem.

Defines the data structures used across all three curriculum layers:
World Seed facts, synthetic episodes with rubrics, and adaptive failure analysis.

References:
    - Piaget stages: https://www.simplypsychology.org/piaget.html
    - Schwartz values: https://pmc.ncbi.nlm.nih.gov/articles/PMC9131418/
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from serhu_orchestrator.personality.types import STAGE_ORDER


# ---------------------------------------------------------------------------
# Layer 1 – World Seed facts
# ---------------------------------------------------------------------------


class WorldSeedFact(BaseModel):
    """A single fact/regularity for bootstrapping the Being's world model.

    Each fact represents a piece of knowledge appropriate for a specific
    Piaget cognitive development stage.
    """

    fact_id: str = Field(description="Unique identifier (e.g. 'sensorimotor_001')")
    stage: str = Field(description="Piaget stage this fact belongs to")
    domain: str = Field(description="Human World Envelope domain")
    fact: str = Field(description="Short declarative knowledge statement")
    examples: list[str] = Field(
        default_factory=list,
        description="Concrete examples illustrating the fact",
    )
    counterexamples: list[str] = Field(
        default_factory=list,
        description="Counterexamples or exceptions to the fact",
    )


# ---------------------------------------------------------------------------
# Layer 2 – Synthetic episodes
# ---------------------------------------------------------------------------


class EpisodeConstraints(BaseModel):
    """Constraints the Being must satisfy when responding."""

    max_words: int | None = Field(
        default=None,
        description="Maximum number of words in the response",
    )
    tone: str | None = Field(
        default=None,
        description="Required emotional tone (e.g. 'curious', 'cautious')",
    )
    format: str | None = Field(
        default=None,
        description="Required output format (e.g. 'single_word', 'question', 'list')",
    )


class SuccessCriterion(BaseModel):
    """An objective boolean check for evaluating the Being's response."""

    criterion_id: str = Field(description="Short identifier")
    description: str = Field(description="Human-readable description of the check")
    check_type: str = Field(
        description="Type of check: 'word_count', 'contains', 'format', 'classification', 'sequence'",
    )
    expected_value: str | None = Field(
        default=None,
        description="Expected value for the check (if applicable)",
    )


class RewardScheme(BaseModel):
    """Scoring rubric for evaluating the Being's response (0.0 to 1.0)."""

    criteria_weights: dict[str, float] = Field(
        default_factory=dict,
        description="Mapping from criterion_id to weight (should sum to 1.0)",
    )
    format_penalty: float = Field(
        default=0.2,
        description="Penalty for violating format constraints",
    )
    stage_adherence_bonus: float = Field(
        default=0.1,
        description="Bonus for responses appropriate to the cognitive stage",
    )


class SyntheticEpisode(BaseModel):
    """A short synthetic interaction episode with rubric and reward scheme.

    Each episode represents a 2-6 turn interaction with verifiable
    success criteria, used to train the Being's internal model.
    """

    episode_id: str = Field(description="Unique identifier")
    stage: str = Field(description="Target Piaget stage")
    domain: str = Field(description="Human World Envelope domain")
    setting: str = Field(description="One-sentence scenario description")
    user_turns: list[str] = Field(description="List of user utterances (2-4 turns)")
    constraints: EpisodeConstraints = Field(
        default_factory=EpisodeConstraints,
        description="Output constraints for the Being",
    )
    success_criteria: list[SuccessCriterion] = Field(
        default_factory=list,
        description="Objective boolean checks for evaluating the response",
    )
    expected_good_response: str = Field(
        description="Example response compatible with the stage",
    )
    common_failure_modes: list[str] = Field(
        default_factory=list,
        description="Typical errors a Being might make",
    )
    reward_scheme: RewardScheme = Field(
        default_factory=RewardScheme,
        description="Scoring rubric for 0.0-1.0 reward",
    )


# ---------------------------------------------------------------------------
# Layer 3 – Adaptive curriculum
# ---------------------------------------------------------------------------


class FailureAnalysis(BaseModel):
    """Analysis of a specific failure pattern for targeted episode generation."""

    failure_id: str = Field(description="Unique identifier for this failure type")
    stage: str = Field(description="Piaget stage where the failure occurs")
    broken_criteria: list[str] = Field(
        description="List of criterion_ids that the Being fails on",
    )
    failure_description: str = Field(
        description="Human-readable description of the failure pattern",
    )
    frequency: int = Field(
        default=1,
        ge=1,
        description="How many times this failure has been observed",
    )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class HumanWorldEnvelope(BaseModel):
    """Ontology of the Human World Envelope – constrains episode domains."""

    domains: list[str] = Field(
        description="List of permitted domain names for episode generation",
    )
    stage_constraints: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Per-stage subset of allowed domains (empty = all domains)",
    )


class CurriculumConfig(BaseModel):
    """Configuration for the curriculum generation pipeline."""

    language: str = Field(
        default="en",
        description="Language code for generated content",
    )
    facts_per_stage: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Number of World Seed facts per stage",
    )
    episodes_per_stage: int = Field(
        default=50,
        ge=5,
        le=200,
        description="Number of synthetic episodes per stage",
    )
    adaptive_batch_size: int = Field(
        default=30,
        ge=5,
        le=100,
        description="Number of episodes generated per adaptive batch",
    )
    target_stages: list[str] = Field(
        default_factory=lambda: list(STAGE_ORDER),
        description="Stages to generate curriculum for",
    )
