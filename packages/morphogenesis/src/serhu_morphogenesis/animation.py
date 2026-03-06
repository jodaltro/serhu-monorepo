"""Animation engine — maps temperament to movement and surface effects.

Movement is driven primarily by TCI-R temperament dimensions:
  - Novelty Seeking (NS) → fast, exploratory movement
  - Harm Avoidance (HA)  → slow, center-hugging, cautious
  - Reward Dependence (RD) → pulse rate (need for connection)
  - Persistence (PS) → steady glow

Surface properties (roughness) follow 16PF-inspired mappings:
  - Harria (tough-minded) → metallic, reflective surfaces
  - Premsia (tender-minded) → matte, diffuse surfaces

References:
    - TCI-R temperament: https://en.wikipedia.org/wiki/Temperament_and_Character_Inventory
    - PBR materials: https://learnopengl.com/PBR/Theory
"""

from __future__ import annotations

from serhu_orchestrator.personality.types import PersonalityState

from serhu_morphogenesis.types import AnimationParams


def compute_animation(state: PersonalityState) -> AnimationParams:
    """Derive animation parameters from the Being's temperament."""
    return AnimationParams(
        pulse_rate=_compute_pulse_rate(state),
        movement_speed=_compute_movement_speed(state),
        center_attraction=_compute_center_attraction(state),
        glow_intensity=_compute_glow_intensity(state),
        roughness=_compute_roughness(state),
    )


def _compute_pulse_rate(state: PersonalityState) -> float:
    """Compute pulse/breathing rate in Hz.

    Driven by Reward Dependence (attachment need) and arousal level.
    Higher RD → faster pulse (seeking connection).
    Sensorimotor Beings pulse slowly.
    """
    tci_t = state.tci_temperament
    hexaco = state.hexaco

    reward_dep = _mean(
        tci_t.sentimentality_rd,
        tci_t.openness_to_communication,
        tci_t.attachment,
        tci_t.dependence_rd,
    )

    arousal = _mean(
        hexaco.liveliness,
        tci_t.exploratory_excitability,
    )

    # Base rate from RD + arousal, mapped to [0.5, 3.0] Hz
    rate = 0.5 + (reward_dep * 0.4 + arousal * 0.6) * 2.5

    # Slow pulse for sensorimotor stage
    if state.development.stage == "sensorimotor":
        rate = min(rate, 1.5)

    return max(0.1, min(5.0, rate))


def _compute_movement_speed(state: PersonalityState) -> float:
    """Compute movement speed through 3D space.

    High Novelty Seeking → fast, exploratory movement.
    High Harm Avoidance → slow, cautious movement.
    """
    tci_t = state.tci_temperament

    novelty_seeking = _mean(
        tci_t.exploratory_excitability,
        tci_t.impulsiveness,
        tci_t.extravagance,
        tci_t.disorderliness,
    )

    harm_avoidance = _mean(
        tci_t.anticipatory_worry,
        tci_t.fear_of_uncertainty,
        tci_t.shyness,
        tci_t.fatigability,
    )

    speed = novelty_seeking * 0.7 + (1.0 - harm_avoidance) * 0.3

    # Early Beings move slowly
    if state.development.stage == "sensorimotor":
        speed *= 0.3

    return max(0.0, min(1.0, speed))


def _compute_center_attraction(state: PersonalityState) -> float:
    """Compute attraction to screen center.

    High Harm Avoidance → stays centered (safe zone).
    High Novelty Seeking → explores screen edges.
    """
    tci_t = state.tci_temperament

    harm_avoidance = _mean(
        tci_t.anticipatory_worry,
        tci_t.fear_of_uncertainty,
        tci_t.shyness,
        tci_t.fatigability,
    )

    novelty_seeking = _mean(
        tci_t.exploratory_excitability,
        tci_t.impulsiveness,
    )

    attraction = harm_avoidance * 0.6 + (1.0 - novelty_seeking) * 0.4
    return max(0.0, min(1.0, attraction))


def _compute_glow_intensity(state: PersonalityState) -> float:
    """Compute glow/emission intensity.

    Driven by Extraversion (liveliness, social boldness) and
    Persistence (steady inner light).
    """
    hexaco = state.hexaco
    tci_t = state.tci_temperament

    extraversion = _mean(
        hexaco.liveliness,
        hexaco.social_boldness,
        hexaco.social_self_esteem,
    )

    persistence = _mean(
        tci_t.eagerness_of_effort,
        tci_t.work_hardened,
        tci_t.ambitious,
    )

    glow = extraversion * 0.7 + persistence * 0.3
    return max(0.0, min(1.0, glow))


def _compute_roughness(state: PersonalityState) -> float:
    """Compute surface roughness for PBR shaders.

    Tough-minded (low sentimentality) → metallic, reflective (low roughness).
    Tender-minded (high sentimentality) → matte, diffuse (high roughness).
    """
    hexaco = state.hexaco

    tenderness = _mean(
        hexaco.sentimentality,
        hexaco.gentleness,
        hexaco.dependence,
    )

    # High tenderness → high roughness (soft, matte)
    # Low tenderness → low roughness (hard, reflective)
    return max(0.0, min(1.0, tenderness))


# -- helpers ----------------------------------------------------------------

def _mean(*values: float) -> float:
    """Compute the arithmetic mean of the given values."""
    if not values:
        return 0.0
    return sum(values) / len(values)
