"""Geometry engine — maps personality traits to shape parameters.

Implements the Kiki/Bouba morphogenesis principle:
  - Agreeable / cooperative personalities → rounded, bulbous forms (Bouba)
  - Assertive / novelty-seeking personalities → angular, spiked forms (Kiki)
  - Conscientiousness → high symmetry, ordered geometry
  - Openness / Creativity → organic noise, fractal complexity
  - Cognitive age → overall complexity (polygon detail)

Shape-trait associations (from the architecture spec):
  Circles/Spheres  → Agreeableness, Cooperativeness
  Squares/Cubes    → Conscientiousness, Order
  Triangles/Spikes → Power, Novelty Seeking
  Spirals/Fractals → Openness, Creativity

References:
    - Kiki/Bouba effect: https://en.wikipedia.org/wiki/Bouba/kiki_effect
    - Shape psychology: https://piktochart.com/blog/psychology-of-shapes/
    - Proc3D framework: https://arxiv.org/html/2601.12234v1
"""

from __future__ import annotations

from serhu_orchestrator.personality.types import PersonalityState, STAGE_AGE_RANGES

from serhu_morphogenesis.types import GeometryProfile


def compute_geometry(state: PersonalityState) -> GeometryProfile:

    """Derive the Being's geometry profile from its personality state.

    Roundness, symmetry, spikiness, and organic noise are driven by
    personality dimensions.  Complexity and scale grow with cognitive age.
    """
    return GeometryProfile(
        roundness=_compute_roundness(state),
        complexity=_compute_complexity(state),
        symmetry=_compute_symmetry(state),
        scale=_compute_scale(state),
        spikiness=_compute_spikiness(state),
        organic_noise=_compute_organic_noise(state),
    )


def _compute_roundness(state: PersonalityState) -> float:
    """Compute roundness from Agreeableness and Cooperativeness.

    High agreeableness → spherical (Bouba).
    Low agreeableness → angular (Kiki).
    """
    hexaco = state.hexaco
    tci_c = state.tci_character

    agreeableness = _mean(
        hexaco.forgiveness,
        hexaco.gentleness,
        hexaco.flexibility,
        hexaco.patience,
    )

    cooperativeness = _mean(
        tci_c.social_acceptance,
        tci_c.empathy,
        tci_c.helpfulness,
        tci_c.compassion,
    )

    # Agreeableness is the primary driver, cooperativeness modulates
    roundness = agreeableness * 0.7 + cooperativeness * 0.3
    return max(0.0, min(1.0, roundness))


def _compute_complexity(state: PersonalityState) -> float:
    """Compute geometric complexity from cognitive development.

    More mature Beings have higher polygon counts and fractal detail.
    Openness/Creativity adds additional complexity.
    """
    dev = state.development
    stage = dev.stage
    age = dev.cognitive_age

    # Stage-based complexity floor
    stage_ranges = STAGE_AGE_RANGES
    if stage in stage_ranges:
        min_age, max_age = stage_ranges[stage]
        age_range = max_age - min_age
        if age_range > 0:
            stage_progress = min(1.0, (age - min_age) / age_range)
        else:
            stage_progress = 1.0
    else:
        stage_progress = 0.0

    # Map stage to complexity range
    stage_base = {
        "sensorimotor": (0.0, 0.2),
        "preoperational": (0.2, 0.4),
        "concrete_operational": (0.4, 0.7),
        "formal_operational": (0.7, 1.0),
    }.get(stage, (0.0, 0.2))

    base_complexity = stage_base[0] + stage_progress * (stage_base[1] - stage_base[0])

    # Openness/Creativity bonus
    openness = _mean(
        state.hexaco.aesthetic_appreciation,
        state.hexaco.inquisitiveness,
        state.hexaco.creativity,
        state.hexaco.unconventionality,
    )
    complexity_bonus = openness * 0.15

    return max(0.0, min(1.0, base_complexity + complexity_bonus))


def _compute_symmetry(state: PersonalityState) -> float:
    """Compute symmetry from Conscientiousness and Order.

    High conscientiousness → perfect bilateral symmetry.
    Low conscientiousness → asymmetric, irregular forms.
    """
    hexaco = state.hexaco

    conscientiousness = _mean(
        hexaco.organization,
        hexaco.diligence,
        hexaco.perfectionism,
        hexaco.prudence,
    )

    return max(0.0, min(1.0, conscientiousness))


def _compute_scale(state: PersonalityState) -> float:
    """Compute overall scale from cognitive development.

    The Being starts as a tiny point and grows as it matures.
    """
    age = state.development.cognitive_age
    # Map 0-192 months to 0.05-1.0 scale
    max_age = 192.0
    scale = 0.05 + (min(age, max_age) / max_age) * 0.95
    return max(0.0, min(1.0, scale))


def _compute_spikiness(state: PersonalityState) -> float:
    """Compute vertex displacement sharpness.

    Driven by Novelty Seeking (angular, risk-taking) and inverted
    Agreeableness (less agreeable → more angular/spiky).
    """
    tci_t = state.tci_temperament
    hexaco = state.hexaco

    novelty_seeking = _mean(
        tci_t.exploratory_excitability,
        tci_t.impulsiveness,
        tci_t.extravagance,
    )

    inv_agreeableness = 1.0 - _mean(
        hexaco.forgiveness,
        hexaco.gentleness,
        hexaco.flexibility,
        hexaco.patience,
    )

    spikiness = novelty_seeking * 0.6 + inv_agreeableness * 0.4
    return max(0.0, min(1.0, spikiness))


def _compute_organic_noise(state: PersonalityState) -> float:
    """Compute simplex noise amplitude for organic 'breathing' effects.

    High Openness and Creativity produce organic, flowing surfaces.
    Self-Transcendence adds additional noise for mystical/fractal patterns.
    """
    hexaco = state.hexaco
    tci_c = state.tci_character

    openness = _mean(
        hexaco.aesthetic_appreciation,
        hexaco.inquisitiveness,
        hexaco.creativity,
        hexaco.unconventionality,
    )

    transcendence = _mean(
        tci_c.self_forgetfulness,
        tci_c.transpersonal_identification,
        tci_c.spiritual_acceptance,
    )

    noise = openness * 0.7 + transcendence * 0.3
    return max(0.0, min(1.0, noise))


# -- helpers ----------------------------------------------------------------

def _mean(*values: float) -> float:
    """Compute the arithmetic mean of the given values."""
    if not values:
        return 0.0
    return sum(values) / len(values)
