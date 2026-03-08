"""Request and response schemas for the API.

These Pydantic models define the JSON contract between the API
and its clients (mobile apps, web frontends, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# -- Being creation ---------------------------------------------------------

class CreateBeingRequest(BaseModel):
    """Request body for creating a new Being."""

    name: str = Field(description="Name given by the user")
    language: str = Field(
        default="en",
        description="Language code (en, pt, es, fr)",
    )


class BeingResponse(BaseModel):
    """Summary response for a Being."""

    being_id: str
    name: str
    language: str
    stage: str = Field(description="Current Piaget cognitive stage")
    cognitive_age: float = Field(description="Cognitive age in months")
    erikson_conflict: str = Field(description="Current Erikson psychosocial conflict")
    interaction_count: int
    is_sleeping: bool = Field(
        default=False,
        description="Whether the Being is currently in continuous sleep mode",
    )


# -- Chat -------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Request body for chatting with a Being."""

    message: str = Field(description="User's message to the Being")
    auto_traits: bool = Field(
        default=True,
        description="Automatically extract trait deltas from the conversation",
    )


class ChatResponse(BaseModel):
    """Response from a chat interaction."""

    response: str = Field(description="The Being's response")
    being_id: str
    stage: str
    cognitive_age: float


# -- Process message (manual) -----------------------------------------------

class ProcessMessageRequest(BaseModel):
    """Request body for processing a message without LLM."""

    role: str = Field(description="Speaker role (user | being | system)")
    content: str = Field(description="Message text")
    metadata: dict | None = Field(default=None, description="Optional metadata")
    trait_deltas: dict[str, dict[str, float]] | None = Field(
        default=None,
        description="Optional personality trait updates",
    )


class ContextWindowResponse(BaseModel):
    """Response with the assembled context window."""

    working_memory_count: int
    archival_count: int
    semantic_facts_count: int


# -- Sleep ------------------------------------------------------------------

class SleepRequest(BaseModel):
    """Request body for triggering a sleep cycle."""

    num_rollouts: int = Field(default=1000, ge=1)
    svd_rank: int = Field(default=8, ge=1)
    cycle_interval_sec: float = Field(
        default=0.1,
        ge=0.0,
        le=60.0,
        description="Interval between continuous sleep cycles in seconds",
    )
    seed: int | None = Field(default=None)


class SleepResponse(BaseModel):
    """Response from starting continuous sleep."""

    is_sleeping: bool = Field(description="Whether the Being is now sleeping")


class WakeRequest(BaseModel):
    """Request body for waking a Being from sleep."""

    timeout: float = Field(
        default=30.0,
        ge=1.0,
        description="Max seconds to wait for the sleep thread to finish",
    )


class WakeResponse(BaseModel):
    """Response from waking a Being."""

    facts_extracted: int
    beliefs_added: int
    hypotheses_generated: int
    cycles_completed: int


class SleepOnceRequest(BaseModel):
    """Request body for triggering a single-shot sleep cycle."""

    num_rollouts: int = Field(default=1000, ge=1)
    svd_rank: int = Field(default=8, ge=1)
    seed: int | None = Field(default=None)


class SleepOnceResponse(BaseModel):
    """Response from a single-shot sleep cycle."""

    facts_extracted: int
    beliefs_added: int
    hypotheses_generated: int


# -- Recall -----------------------------------------------------------------

class RecallRequest(BaseModel):
    """Request body for recalling memories."""

    query: str = Field(description="Natural-language query")
    top_k: int = Field(default=5, ge=1, le=100)
    memory_type: str | None = Field(
        default=None,
        description="Optional filter (episodic | semantic | causal)",
    )


class RecallResponse(BaseModel):
    """Response with recalled memories."""

    memories: list[dict]


# -- Learn fact -------------------------------------------------------------

class LearnFactRequest(BaseModel):
    """Request body for storing a semantic fact."""

    fact: str = Field(description="Distilled knowledge statement")


class LearnFactResponse(BaseModel):
    """Response from storing a fact."""

    stored: bool


# -- Visual state -----------------------------------------------------------

class VisualStateResponse(BaseModel):
    """Visual morphogenesis state for the renderer."""

    being_id: str
    cognitive_stage: str
    cognitive_age: float

    # Color
    hue: float
    saturation: float
    lightness: float
    alpha: float

    # Geometry
    roundness: float
    complexity: float
    symmetry: float
    scale: float
    spikiness: float
    organic_noise: float

    # Animation
    pulse_rate: float
    movement_speed: float
    center_attraction: float
    glow_intensity: float
    roughness: float


# -- Personality state (detailed) -------------------------------------------

class PersonalityResponse(BaseModel):
    """Full personality state dump."""

    being_id: str
    name: str
    language: str
    stage: str
    cognitive_age: float
    erikson_conflict: str
    interaction_count: int
    milestones_achieved: list[str]
    hexaco: dict[str, float]
    tci_temperament: dict[str, float]
    tci_character: dict[str, float]
    schwartz: dict[str, float]
    core_beliefs: list[str]
    surface_beliefs: list[str]
