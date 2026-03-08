"""Curriculum – World Seed, synthetic episodes, and adaptive learning.

Implements a three-layer curriculum system for bootstrapping a Being's
knowledge without waiting for real user interactions:

1. **World Seed** (Layer 1) – Static human-world facts per Piaget stage.
2. **Synthetic Episodes** (Layer 2) – Short interaction episodes with rubrics.
3. **Adaptive Curriculum** (Layer 3) – Targeted episodes attacking specific failures.

The Human World Envelope constrains all generated content to 6 plausible
everyday domains, ensuring the Being's initial world model is grounded
in common human experience.

References:
    - Piaget stages: https://www.simplypsychology.org/piaget.html
    - Zone of Proximal Development: https://en.wikipedia.org/wiki/Zone_of_proximal_development
"""

from serhu_orchestrator.curriculum.types import (
    CurriculumConfig,
    EpisodeConstraints,
    FailureAnalysis,
    HumanWorldEnvelope,
    RewardScheme,
    SuccessCriterion,
    SyntheticEpisode,
    WorldSeedFact,
)
from serhu_orchestrator.curriculum.envelope import HUMAN_WORLD_ENVELOPE, Domain
from serhu_orchestrator.curriculum.world_seed import get_world_seed, get_world_seed_facts
from serhu_orchestrator.curriculum.episodes import generate_synthetic_episodes
from serhu_orchestrator.curriculum.adaptive import generate_adaptive_episodes

__all__ = [
    "CurriculumConfig",
    "Domain",
    "EpisodeConstraints",
    "FailureAnalysis",
    "HUMAN_WORLD_ENVELOPE",
    "HumanWorldEnvelope",
    "RewardScheme",
    "SuccessCriterion",
    "SyntheticEpisode",
    "WorldSeedFact",
    "generate_adaptive_episodes",
    "generate_synthetic_episodes",
    "get_world_seed",
    "get_world_seed_facts",
]
