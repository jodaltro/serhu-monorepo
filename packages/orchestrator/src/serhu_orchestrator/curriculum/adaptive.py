"""Adaptive Curriculum – Layer 3: targeted episode generation.

Generates episodes that specifically target the Being's failure patterns.
Uses failure analysis to create focused training material that attacks
weaknesses in the Zone of Proximal Development.

The adaptive layer does NOT generate random episodes; it analyzes
which rubric criteria the Being fails on and produces episodes that
specifically exercise those criteria with contextual variation.

References:
    - Zone of Proximal Development (Vygotsky):
      https://en.wikipedia.org/wiki/Zone_of_proximal_development
    - Curriculum learning: https://arxiv.org/abs/2101.10382
"""

from __future__ import annotations

import logging
import random

from serhu_orchestrator.curriculum.types import (
    EpisodeConstraints,
    FailureAnalysis,
    RewardScheme,
    SuccessCriterion,
    SyntheticEpisode,
)
from serhu_orchestrator.curriculum.envelope import (
    ALL_DOMAINS,
    get_stage_vocabulary,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Failure → episode templates
# ---------------------------------------------------------------------------

# Map from check_type to episode-generation strategies
_FAILURE_TEMPLATES: dict[str, dict] = {
    "word_count": {
        "description": "The Being produces responses that are too long or too short.",
        "remediation": "Enforce strict word count limits with varied contexts.",
    },
    "contains": {
        "description": "The Being fails to include required content.",
        "remediation": "Present stimuli that strongly prime the target content.",
    },
    "format": {
        "description": "The Being does not follow the required output format.",
        "remediation": "Practice specific formats with explicit examples.",
    },
    "classification": {
        "description": "The Being misclassifies items.",
        "remediation": "Present clear classification tasks with known answers.",
    },
    "sequence": {
        "description": "The Being fails to order items correctly.",
        "remediation": "Practice sequencing with simple, unambiguous orders.",
    },
}


def _generate_word_count_episodes(
    failure: FailureAnalysis,
    count: int,
    seed: int | None,
) -> list[SyntheticEpisode]:
    """Generate episodes targeting word count adherence."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    stage = failure.stage
    vocab = get_stage_vocabulary("everyday_objects", stage) + get_stage_vocabulary("physical_actions", stage)

    if not vocab:
        vocab = ["thing", "object", "action"]

    limits = [1, 2, 3, 5] if stage == "sensorimotor" else [5, 8, 10, 15]

    for i in range(count):
        max_words = rng.choice(limits)
        word = rng.choice(vocab)
        episodes.append(SyntheticEpisode(
            episode_id=f"adaptive_wc_{stage}_{i+1:03d}",
            stage=stage,
            domain=rng.choice(["everyday_objects", "physical_actions", "communication"]),
            setting=f"Practice responding about '{word}' with exactly {max_words} words or fewer.",
            user_turns=[f"Tell me about {word}.", f"Use {max_words} words or fewer."],
            constraints=EpisodeConstraints(max_words=max_words),
            success_criteria=[
                SuccessCriterion(
                    criterion_id="word_count",
                    description=f"Response has <={max_words} words",
                    check_type="word_count",
                    expected_value=f"<={max_words}",
                ),
            ],
            expected_good_response=f"{word}." if max_words <= 2 else f"The {word} is interesting.",
            common_failure_modes=["Exceeding word count", "Empty response"],
            reward_scheme=RewardScheme(criteria_weights={"word_count": 1.0}),
        ))

    return episodes


def _generate_contains_episodes(
    failure: FailureAnalysis,
    count: int,
    seed: int | None,
) -> list[SyntheticEpisode]:
    """Generate episodes targeting content inclusion."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    stage = failure.stage
    vocab = get_stage_vocabulary("everyday_objects", stage)

    if not vocab:
        vocab = ["object", "thing", "item"]

    for i in range(count):
        target = rng.choice(vocab)
        episodes.append(SyntheticEpisode(
            episode_id=f"adaptive_ct_{stage}_{i+1:03d}",
            stage=stage,
            domain="communication",
            setting=f"The user talks about '{target}' and expects a response mentioning it.",
            user_turns=[f"Let's talk about {target}.", f"What do you think about {target}?"],
            constraints=EpisodeConstraints(
                max_words=10 if stage in ("sensorimotor", "preoperational") else 30,
            ),
            success_criteria=[
                SuccessCriterion(
                    criterion_id="contains_target",
                    description=f"Response mentions '{target}'",
                    check_type="contains",
                    expected_value=target,
                ),
            ],
            expected_good_response=f"{target}!" if stage == "sensorimotor" else f"I like {target}.",
            common_failure_modes=[f"Not mentioning '{target}'", "Off-topic response"],
            reward_scheme=RewardScheme(criteria_weights={"contains_target": 1.0}),
        ))

    return episodes


def _generate_format_episodes(
    failure: FailureAnalysis,
    count: int,
    seed: int | None,
) -> list[SyntheticEpisode]:
    """Generate episodes targeting format adherence."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    stage = failure.stage

    formats = {
        "sensorimotor": ["sound", "exclamation", "single_word"],
        "preoperational": ["question", "single_word", "list"],
        "concrete_operational": ["steps", "comparison", "question"],
        "formal_operational": ["hypothesis", "evaluation", "analogy"],
    }

    stage_formats = formats.get(stage, ["fragment"])

    for i in range(count):
        fmt = rng.choice(stage_formats)
        episodes.append(SyntheticEpisode(
            episode_id=f"adaptive_fmt_{stage}_{i+1:03d}",
            stage=stage,
            domain="communication",
            setting=f"Practice producing a response in '{fmt}' format.",
            user_turns=[f"Respond to this in {fmt} format.", "Go ahead!"],
            constraints=EpisodeConstraints(format=fmt),
            success_criteria=[
                SuccessCriterion(
                    criterion_id="format_check",
                    description=f"Response follows '{fmt}' format",
                    check_type="format",
                    expected_value=fmt,
                ),
            ],
            expected_good_response=f"(Example {fmt} response)",
            common_failure_modes=[f"Wrong format (not {fmt})", "No response"],
            reward_scheme=RewardScheme(criteria_weights={"format_check": 1.0}),
        ))

    return episodes


def _generate_classification_episodes(
    failure: FailureAnalysis,
    count: int,
    seed: int | None,
) -> list[SyntheticEpisode]:
    """Generate episodes targeting classification accuracy."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    stage = failure.stage

    categories = {
        "preoperational": [
            (["dog", "cat", "bird"], "animal"),
            (["car", "ball", "block"], "toy"),
            (["apple", "banana", "bread"], "food"),
        ],
        "concrete_operational": [
            (["dog", "whale", "bat"], "mammal"),
            (["eagle", "penguin", "sparrow"], "bird"),
            (["salmon", "goldfish", "shark"], "fish"),
        ],
        "formal_operational": [
            (["democracy", "monarchy", "republic"], "government"),
            (["novel", "poem", "essay"], "literature"),
            (["addition", "multiplication", "division"], "math_operation"),
        ],
    }

    stage_cats = categories.get(stage, categories["preoperational"])

    for i in range(count):
        items, category = rng.choice(stage_cats)
        item = rng.choice(items)
        episodes.append(SyntheticEpisode(
            episode_id=f"adaptive_cls_{stage}_{i+1:03d}",
            stage=stage,
            domain="tasks_and_rules",
            setting=f"Classify '{item}' into the correct category.",
            user_turns=[f"What category does '{item}' belong to?", f"Choose from: {category} or other."],
            constraints=EpisodeConstraints(max_words=10),
            success_criteria=[
                SuccessCriterion(
                    criterion_id="correct_class",
                    description=f"Correctly classifies as '{category}'",
                    check_type="classification",
                    expected_value=category,
                ),
            ],
            expected_good_response=f"'{item}' is a {category}.",
            common_failure_modes=["Wrong category", "No classification given"],
            reward_scheme=RewardScheme(criteria_weights={"correct_class": 1.0}),
        ))

    return episodes


def _generate_sequence_episodes(
    failure: FailureAnalysis,
    count: int,
    seed: int | None,
) -> list[SyntheticEpisode]:
    """Generate episodes targeting sequence ordering."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    stage = failure.stage

    sequences = [
        (["wake up", "eat breakfast", "go to school"], "daily routine"),
        (["plant seed", "water it", "watch it grow"], "growing a plant"),
        (["get ingredients", "mix them", "bake the cake"], "baking"),
        (["read the problem", "think about it", "write the answer"], "solving a problem"),
    ]

    for i in range(count):
        steps, context = rng.choice(sequences)
        episodes.append(SyntheticEpisode(
            episode_id=f"adaptive_seq_{stage}_{i+1:03d}",
            stage=stage,
            domain="tasks_and_rules",
            setting=f"Put the steps of '{context}' in the correct order.",
            user_turns=[
                f"What is the correct order for {context}?",
                f"The steps are: {', '.join(rng.sample(steps, len(steps)))}",
            ],
            constraints=EpisodeConstraints(max_words=20),
            success_criteria=[
                SuccessCriterion(
                    criterion_id="correct_order",
                    description="Steps are in the correct order",
                    check_type="sequence",
                ),
            ],
            expected_good_response=f"1. {steps[0]} 2. {steps[1]} 3. {steps[2]}",
            common_failure_modes=["Wrong order", "Missing steps"],
            reward_scheme=RewardScheme(criteria_weights={"correct_order": 1.0}),
        ))

    return episodes


# ---------------------------------------------------------------------------
# Generator dispatch
# ---------------------------------------------------------------------------

_FAILURE_GENERATORS: dict[str, callable] = {
    "word_count": _generate_word_count_episodes,
    "contains": _generate_contains_episodes,
    "format": _generate_format_episodes,
    "classification": _generate_classification_episodes,
    "sequence": _generate_sequence_episodes,
}


def generate_adaptive_episodes(
    failures: list[FailureAnalysis],
    *,
    batch_size: int = 30,
    seed: int | None = None,
) -> list[SyntheticEpisode]:
    """Generate targeted episodes that address specific failure patterns.

    Distributes the batch across all identified failures, weighted by
    their frequency.

    Parameters
    ----------
    failures : list[FailureAnalysis]
        Identified failure patterns to target.
    batch_size : int
        Total number of episodes to generate.
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    list[SyntheticEpisode]
        Targeted episodes attacking the identified failures.
    """
    if not failures:
        logger.warning("generate_adaptive_episodes: no failures provided")
        return []

    # Weight episodes by failure frequency
    total_freq = sum(f.frequency for f in failures)
    episodes: list[SyntheticEpisode] = []

    for failure in failures:
        # Allocate episodes proportionally to failure frequency
        allocated = max(1, round(batch_size * failure.frequency / total_freq))

        # Determine which generator to use based on broken criteria
        for criterion_id in failure.broken_criteria:
            # Find the check_type for this criterion
            generator = _FAILURE_GENERATORS.get(criterion_id)
            if generator is not None:
                count = max(1, allocated // len(failure.broken_criteria))
                generated = generator(failure, count, seed)
                episodes.extend(generated)
                logger.info(
                    "Adaptive: %d episodes for failure '%s' (criterion: %s)",
                    len(generated), failure.failure_id, criterion_id,
                )

    # Trim to batch size
    if len(episodes) > batch_size:
        rng = random.Random(seed)
        episodes = rng.sample(episodes, batch_size)

    logger.info("Adaptive curriculum: %d total episodes for %d failures", len(episodes), len(failures))
    return episodes
