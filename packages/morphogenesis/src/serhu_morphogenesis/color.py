"""Color engine — maps personality traits to color profiles.

Implements the color-personality mapping from the cognitive architecture spec:
  - Hue is driven by the dominant personality dimension.
  - Saturation reflects arousal/excitement level.
  - Lightness captures emotional valence (positive/negative).

Color-trait associations:
  Red (0°)    → Extraversion, dominance, passion
  Yellow (60°) → Agreeableness, optimism
  Green (120°) → Reward Dependence, harmony
  Blue (210°)  → Emotional stability, trust, wisdom
  Purple (270°) → Self-Transcendence, spirituality
  Grey         → Neuroticism, withdrawal (low saturation)

References:
    - Color-personality: https://pmc.ncbi.nlm.nih.gov/articles/PMC9806338/
    - Color psychology: https://nathatype.com/color-psychology-in-art-how-colors-shape-emotions-and-creativity/
    - Arousal-saturation link: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.854574/full
"""

from __future__ import annotations

from serhu_orchestrator.personality.types import PersonalityState

from serhu_morphogenesis.types import ColorProfile

# Maximum age ranges for the Piaget stages (months)
_STAGE_MAX_AGE: dict[str, float] = {
    "sensorimotor": 24.0,
    "preoperational": 84.0,
    "concrete_operational": 132.0,
    "formal_operational": 192.0,
}


def compute_color(state: PersonalityState) -> ColorProfile:
    """Derive the Being's color profile from its personality state.

    The dominant personality dimension determines the base hue.
    Saturation and lightness are driven by arousal and emotional valence.
    Alpha increases with cognitive development (newborns are translucent).
    """
    hue = _compute_hue(state)
    saturation = _compute_saturation(state)
    lightness = _compute_lightness(state)
    alpha = _compute_alpha(state)

    return ColorProfile(
        hue=hue,
        saturation=saturation,
        lightness=lightness,
        alpha=alpha,
    )


def _compute_hue(state: PersonalityState) -> float:
    """Compute the dominant hue from personality trait dimensions.

    Each personality dimension contributes a weighted vote toward a
    specific hue.  The final hue is a weighted circular average.
    """
    hexaco = state.hexaco
    tci_t = state.tci_temperament
    tci_c = state.tci_character
    schwartz = state.schwartz

    # Extraversion → Red (0°)
    extraversion = _mean(
        hexaco.social_self_esteem,
        hexaco.social_boldness,
        hexaco.sociability,
        hexaco.liveliness,
    )

    # Agreeableness → Yellow (60°)
    agreeableness = _mean(
        hexaco.forgiveness,
        hexaco.gentleness,
        hexaco.flexibility,
        hexaco.patience,
    )

    # Reward Dependence → Green (120°)
    reward_dep = _mean(
        tci_t.sentimentality_rd,
        tci_t.openness_to_communication,
        tci_t.attachment,
        tci_t.dependence_rd,
    )

    # Emotionality (stability) → Blue (210°)
    # Inverted: high stability = low emotionality → blue
    emotionality = _mean(
        hexaco.fearfulness,
        hexaco.anxiety,
        hexaco.dependence,
        hexaco.sentimentality,
    )
    stability = 1.0 - emotionality

    # Self-Transcendence → Purple (270°)
    transcendence = _mean(
        tci_c.self_forgetfulness,
        tci_c.transpersonal_identification,
        tci_c.spiritual_acceptance,
        schwartz.universalism_concern,
        schwartz.universalism_nature,
    )

    # Weighted circular average
    hue_weights = [
        (0.0, extraversion),       # Red
        (60.0, agreeableness),     # Yellow
        (120.0, reward_dep),       # Green
        (210.0, stability),        # Blue
        (270.0, transcendence),    # Purple
    ]

    return _circular_weighted_mean(hue_weights)


def _compute_saturation(state: PersonalityState) -> float:
    """Compute saturation from arousal/excitement level.

    High arousal (Extraversion, Novelty Seeking) → high saturation.
    Low arousal (Harm Avoidance, low liveliness) → desaturated/muted.
    Newborn Beings (sensorimotor) start with very low saturation.
    """
    hexaco = state.hexaco
    tci_t = state.tci_temperament

    # Arousal contributors
    novelty_seeking = _mean(
        tci_t.exploratory_excitability,
        tci_t.impulsiveness,
        tci_t.extravagance,
    )
    liveliness = hexaco.liveliness
    harm_avoidance = _mean(
        tci_t.anticipatory_worry,
        tci_t.fear_of_uncertainty,
        tci_t.shyness,
        tci_t.fatigability,
    )

    arousal = (novelty_seeking * 0.4 + liveliness * 0.3 + (1.0 - harm_avoidance) * 0.3)

    # Stage-based damping: early Beings are muted regardless of trait scores
    stage = state.development.stage
    stage_multiplier = {
        "sensorimotor": 0.2,
        "preoperational": 0.5,
        "concrete_operational": 0.8,
        "formal_operational": 1.0,
    }.get(stage, 0.2)

    return max(0.0, min(1.0, arousal * stage_multiplier))


def _compute_lightness(state: PersonalityState) -> float:
    """Compute lightness from emotional valence.

    Positive emotions → high lightness (bright).
    Negative emotions → low lightness (dark).
    Newborn Beings start bright (white point).
    """
    hexaco = state.hexaco

    # Positive valence contributors
    positive = _mean(
        hexaco.liveliness,
        hexaco.social_self_esteem,
        hexaco.forgiveness,
        hexaco.gentleness,
    )

    # Negative valence contributors
    negative = _mean(
        hexaco.anxiety,
        hexaco.fearfulness,
    )

    # Valence: 0.0 (dark) to 1.0 (bright)
    valence = positive * 0.6 + (1.0 - negative) * 0.4

    # Map to lightness range [0.2, 0.9]
    lightness = 0.2 + valence * 0.7

    # Newborns are bright (white point)
    if state.development.stage == "sensorimotor":
        age_fraction = state.development.cognitive_age / 24.0
        lightness = 1.0 - age_fraction * (1.0 - lightness)

    return max(0.0, min(1.0, lightness))


def _compute_alpha(state: PersonalityState) -> float:
    """Compute opacity from cognitive development.

    Newborn Beings are translucent; they become more opaque
    as they develop and solidify their identity.
    """
    stage = state.development.stage
    age = state.development.cognitive_age

    max_age = _STAGE_MAX_AGE.get(stage, 192.0)
    progress = min(1.0, age / max_age) if max_age > 0 else 1.0

    # Alpha range: 0.3 (newborn) → 1.0 (fully developed)
    return 0.3 + progress * 0.7


# -- helpers ----------------------------------------------------------------

def _mean(*values: float) -> float:
    """Compute the arithmetic mean of the given values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


import math


def _circular_weighted_mean(hue_weights: list[tuple[float, float]]) -> float:
    """Compute a weighted circular mean of hue angles.

    Each entry is ``(hue_degrees, weight)``.  Returns a hue in [0, 360).
    """
    total_weight = sum(w for _, w in hue_weights)
    if total_weight == 0:
        return 0.0

    sin_sum = 0.0
    cos_sum = 0.0
    for hue_deg, weight in hue_weights:
        rad = math.radians(hue_deg)
        sin_sum += weight * math.sin(rad)
        cos_sum += weight * math.cos(rad)

    avg_rad = math.atan2(sin_sum / total_weight, cos_sum / total_weight)
    avg_deg = math.degrees(avg_rad) % 360.0
    return avg_deg
