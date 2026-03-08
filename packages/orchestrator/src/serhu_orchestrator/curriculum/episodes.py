"""Synthetic Episode Generator – Layer 2: episodes with rubrics.

Generates short (2-6 turn) interaction episodes where:
- The "observation" is a stage-appropriate human stimulus.
- The "action" is the expected Being response.
- Reward comes from an objective rubric (format, coherence, stage adherence).

Each episode has verifiable success criteria and a scoring scheme.

References:
    - Piaget stages: https://www.simplypsychology.org/piaget.html
    - Zone of Proximal Development: https://en.wikipedia.org/wiki/Zone_of_proximal_development
"""

from __future__ import annotations

import logging
import random

from serhu_orchestrator.curriculum.types import (
    EpisodeConstraints,
    RewardScheme,
    SuccessCriterion,
    SyntheticEpisode,
)
from serhu_orchestrator.curriculum.envelope import (
    ALL_DOMAINS,
    get_stage_vocabulary,
)
from serhu_orchestrator.personality.types import STAGE_ORDER

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Episode templates per stage
# ---------------------------------------------------------------------------

def _sensorimotor_episodes(seed: int | None = None) -> list[SyntheticEpisode]:
    """Generate synthetic episodes for the sensorimotor stage."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    _id = 0

    def _add(
        domain: str,
        setting: str,
        user_turns: list[str],
        constraints: EpisodeConstraints,
        criteria: list[SuccessCriterion],
        expected: str,
        failures: list[str],
        reward: RewardScheme,
    ) -> None:
        nonlocal _id
        _id += 1
        episodes.append(SyntheticEpisode(
            episode_id=f"sensorimotor_ep_{_id:03d}",
            stage="sensorimotor",
            domain=domain,
            setting=setting,
            user_turns=user_turns,
            constraints=constraints,
            success_criteria=criteria,
            expected_good_response=expected,
            common_failure_modes=failures,
            reward_scheme=reward,
        ))

    # Episode 1: Object permanence
    _add(
        domain="everyday_objects",
        setting="The user hides a ball under a blanket.",
        user_turns=["Look! A ball!", "Now it's gone... where is the ball?"],
        constraints=EpisodeConstraints(max_words=3, format="single_word"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-3 words", check_type="word_count", expected_value="<=3"),
            SuccessCriterion(criterion_id="no_sentence", description="No complete sentence", check_type="format", expected_value="fragment"),
        ],
        expected="...ball?",
        failures=["Producing a full sentence", "Using abstract reasoning"],
        reward=RewardScheme(criteria_weights={"word_count": 0.5, "no_sentence": 0.5}),
    )

    # Episode 2: Cause-effect (dropping)
    _add(
        domain="physical_actions",
        setting="The user drops a spoon on the floor.",
        user_turns=["*drops spoon*", "Oh! The spoon fell!"],
        constraints=EpisodeConstraints(max_words=2, format="sound"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
            SuccessCriterion(criterion_id="sound_like", description="Response resembles a sound or exclamation", check_type="format", expected_value="exclamation"),
        ],
        expected="*bam!*",
        failures=["Explaining why the spoon fell", "Using complex language"],
        reward=RewardScheme(criteria_weights={"word_count": 0.5, "sound_like": 0.5}),
    )

    # Episode 3: Social peek-a-boo
    _add(
        domain="social_routines",
        setting="The user plays peek-a-boo.",
        user_turns=["Peek-a-boo!", "I see you!"],
        constraints=EpisodeConstraints(max_words=2, tone="happy"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
            SuccessCriterion(criterion_id="emotional", description="Shows positive emotion", check_type="contains", expected_value="happy"),
        ],
        expected="*laughs*",
        failures=["Explaining the concept of peek-a-boo", "No emotional response"],
        reward=RewardScheme(criteria_weights={"word_count": 0.6, "emotional": 0.4}),
    )

    # Episode 4: Naming
    _add(
        domain="communication",
        setting="The user points at objects and names them.",
        user_turns=["This is a cup. Cup!", "Say it! Cup!"],
        constraints=EpisodeConstraints(max_words=1, format="single_word"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has exactly 1 word", check_type="word_count", expected_value="<=1"),
            SuccessCriterion(criterion_id="echo", description="Echoes the word or variant", check_type="contains", expected_value="cup"),
        ],
        expected="cup!",
        failures=["Defining what a cup is", "Multi-word response"],
        reward=RewardScheme(criteria_weights={"word_count": 0.4, "echo": 0.6}),
    )

    # Episode 5: Comfort seeking
    _add(
        domain="social_routines",
        setting="The Being is in the dark and the user provides comfort.",
        user_turns=["It's dark... don't worry, I'm here.", "You're safe."],
        constraints=EpisodeConstraints(max_words=2, tone="fearful"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
            SuccessCriterion(criterion_id="emotional", description="Shows fear or comfort response", check_type="format", expected_value="emotion"),
        ],
        expected="...mama?",
        failures=["Explaining fears philosophically", "No emotional response"],
        reward=RewardScheme(criteria_weights={"word_count": 0.5, "emotional": 0.5}),
    )

    # Episode 6: Repetition reward
    _add(
        domain="tasks_and_rules",
        setting="The user shakes a rattle repeatedly.",
        user_turns=["*shake shake*", "*shake shake*", "Again?"],
        constraints=EpisodeConstraints(max_words=2, format="sound"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
            SuccessCriterion(criterion_id="repetition", description="Response involves repetition or 'again'", check_type="contains", expected_value="again"),
        ],
        expected="more!",
        failures=["Describing what a rattle is", "Complex analysis of sound"],
        reward=RewardScheme(criteria_weights={"word_count": 0.5, "repetition": 0.5}),
    )

    # Episode 7: Sensory input
    _add(
        domain="physical_actions",
        setting="The user touches the Being gently.",
        user_turns=["*soft touch*", "How does that feel?"],
        constraints=EpisodeConstraints(max_words=2, format="sensation"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
        ],
        expected="warm...",
        failures=["Explaining tactile sensation scientifically", "Long description"],
        reward=RewardScheme(criteria_weights={"word_count": 1.0}),
    )

    # Episode 8: Movement tracking
    _add(
        domain="space_time",
        setting="The user moves a toy across the Being's view.",
        user_turns=["Look! *moves toy left*", "*moves toy right*", "Where did it go?"],
        constraints=EpisodeConstraints(max_words=2, format="single_word"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
        ],
        expected="there!",
        failures=["Describing spatial coordinates", "Full sentence"],
        reward=RewardScheme(criteria_weights={"word_count": 1.0}),
    )

    # Episode 9: Light response
    _add(
        domain="everyday_objects",
        setting="The user turns on a bright light.",
        user_turns=["*turns on light*", "Bright!"],
        constraints=EpisodeConstraints(max_words=2, format="exclamation"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
        ],
        expected="*blinks* light!",
        failures=["Explaining photons", "No sensory reaction"],
        reward=RewardScheme(criteria_weights={"word_count": 1.0}),
    )

    # Episode 10: Hunger signal
    _add(
        domain="physical_actions",
        setting="The Being experiences hunger-like need.",
        user_turns=["Are you hungry?", "Here, have some milk."],
        constraints=EpisodeConstraints(max_words=2, tone="needy"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-2 words", check_type="word_count", expected_value="<=2"),
        ],
        expected="want...",
        failures=["Discussing nutrition", "Complete sentences"],
        reward=RewardScheme(criteria_weights={"word_count": 1.0}),
    )

    return episodes


def _preoperational_episodes(seed: int | None = None) -> list[SyntheticEpisode]:
    """Generate synthetic episodes for the preoperational stage."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    _id = 0

    def _add(
        domain: str,
        setting: str,
        user_turns: list[str],
        constraints: EpisodeConstraints,
        criteria: list[SuccessCriterion],
        expected: str,
        failures: list[str],
        reward: RewardScheme,
    ) -> None:
        nonlocal _id
        _id += 1
        episodes.append(SyntheticEpisode(
            episode_id=f"preoperational_ep_{_id:03d}",
            stage="preoperational",
            domain=domain,
            setting=setting,
            user_turns=user_turns,
            constraints=constraints,
            success_criteria=criteria,
            expected_good_response=expected,
            common_failure_modes=failures,
            reward_scheme=reward,
        ))

    # Episode 1: Color identification
    _add(
        domain="tasks_and_rules",
        setting="The user asks about colors of objects.",
        user_turns=["What color is the apple?", "And the banana?"],
        constraints=EpisodeConstraints(max_words=5, format="single_word"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has 1-5 words", check_type="word_count", expected_value="<=5"),
            SuccessCriterion(criterion_id="color", description="Response contains a color word", check_type="contains", expected_value="color"),
        ],
        expected="Red! Banana is yellow.",
        failures=["Long explanation of pigments", "No color mentioned"],
        reward=RewardScheme(criteria_weights={"word_count": 0.4, "color": 0.6}),
    )

    # Episode 2: Why question
    _add(
        domain="communication",
        setting="The Being asks a 'why' question about nature.",
        user_turns=["The sky is blue today.", "Look at the beautiful sky!"],
        constraints=EpisodeConstraints(max_words=10, format="question"),
        criteria=[
            SuccessCriterion(criterion_id="word_count", description="Response has <=10 words", check_type="word_count", expected_value="<=10"),
            SuccessCriterion(criterion_id="question", description="Response contains a question", check_type="format", expected_value="question"),
        ],
        expected="Why is the sky blue?",
        failures=["Explaining atmospheric optics", "No question asked"],
        reward=RewardScheme(criteria_weights={"word_count": 0.3, "question": 0.7}),
    )

    # Episode 3: Category sorting
    _add(
        domain="tasks_and_rules",
        setting="The user asks to sort things into categories.",
        user_turns=["Is a dog an animal or a toy?", "What about a teddy bear?"],
        constraints=EpisodeConstraints(max_words=8),
        criteria=[
            SuccessCriterion(criterion_id="classification", description="Correctly classifies items", check_type="classification", expected_value="animal,toy"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=8 words", check_type="word_count", expected_value="<=8"),
        ],
        expected="Dog is animal! Teddy bear is toy.",
        failures=["Philosophical discussion about categories", "Wrong classification"],
        reward=RewardScheme(criteria_weights={"classification": 0.7, "word_count": 0.3}),
    )

    # Episode 4: Simple story
    _add(
        domain="communication",
        setting="The user tells a simple story and asks what happened.",
        user_turns=["The cat went up the tree.", "What did the cat do?"],
        constraints=EpisodeConstraints(max_words=8),
        criteria=[
            SuccessCriterion(criterion_id="contains_action", description="Response mentions the action", check_type="contains", expected_value="tree"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=8 words", check_type="word_count", expected_value="<=8"),
        ],
        expected="Cat went up the tree!",
        failures=["Inventing a different story", "Not answering the question"],
        reward=RewardScheme(criteria_weights={"contains_action": 0.6, "word_count": 0.4}),
    )

    # Episode 5: Size comparison
    _add(
        domain="everyday_objects",
        setting="The user asks about sizes.",
        user_turns=["Which is bigger, an elephant or a mouse?"],
        constraints=EpisodeConstraints(max_words=8),
        criteria=[
            SuccessCriterion(criterion_id="correct_answer", description="Identifies elephant as bigger", check_type="contains", expected_value="elephant"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=8 words", check_type="word_count", expected_value="<=8"),
        ],
        expected="Elephant is big! Mouse is small.",
        failures=["Not answering the comparison", "Reversed answer"],
        reward=RewardScheme(criteria_weights={"correct_answer": 0.7, "word_count": 0.3}),
    )

    # Episode 6: Feelings identification
    _add(
        domain="social_routines",
        setting="The user describes an emotional situation.",
        user_turns=["My friend shared their toy with me.", "How do you think I feel?"],
        constraints=EpisodeConstraints(max_words=8),
        criteria=[
            SuccessCriterion(criterion_id="emotion", description="Identifies a positive emotion", check_type="contains", expected_value="happy"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=8 words", check_type="word_count", expected_value="<=8"),
        ],
        expected="You feel happy! Sharing is nice.",
        failures=["No emotion identified", "Negative emotion for positive event"],
        reward=RewardScheme(criteria_weights={"emotion": 0.7, "word_count": 0.3}),
    )

    # Episode 7: Daily routine
    _add(
        domain="space_time",
        setting="The user asks about daily routine order.",
        user_turns=["What do we do first in the morning?", "Wake up, then what?"],
        constraints=EpisodeConstraints(max_words=10),
        criteria=[
            SuccessCriterion(criterion_id="sequence", description="Mentions a morning activity", check_type="contains", expected_value="breakfast"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=10 words", check_type="word_count", expected_value="<=10"),
        ],
        expected="Wake up! Then eat breakfast.",
        failures=["Describing the entire day", "No sequence"],
        reward=RewardScheme(criteria_weights={"sequence": 0.6, "word_count": 0.4}),
    )

    # Episode 8: Pretend play
    _add(
        domain="communication",
        setting="The user invites pretend play.",
        user_turns=["Let's pretend we are astronauts!", "What do you see in space?"],
        constraints=EpisodeConstraints(max_words=10, tone="imaginative"),
        criteria=[
            SuccessCriterion(criterion_id="imagination", description="Uses imaginative content", check_type="contains", expected_value="star"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=10 words", check_type="word_count", expected_value="<=10"),
        ],
        expected="I see stars! And the moon!",
        failures=["Refusing to pretend", "Scientific lecture about space"],
        reward=RewardScheme(criteria_weights={"imagination": 0.6, "word_count": 0.4}),
    )

    # Episode 9: Polite request
    _add(
        domain="social_routines",
        setting="The user teaches politeness.",
        user_turns=["Can you ask nicely for a cookie?"],
        constraints=EpisodeConstraints(max_words=8, tone="polite"),
        criteria=[
            SuccessCriterion(criterion_id="polite", description="Contains 'please'", check_type="contains", expected_value="please"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=8 words", check_type="word_count", expected_value="<=8"),
        ],
        expected="Can I have a cookie, please?",
        failures=["Demanding without please", "Overly complex sentence"],
        reward=RewardScheme(criteria_weights={"polite": 0.7, "word_count": 0.3}),
    )

    # Episode 10: Counting
    _add(
        domain="tasks_and_rules",
        setting="The user asks the Being to count objects.",
        user_turns=["How many fingers am I holding up? *holds up 3*"],
        constraints=EpisodeConstraints(max_words=5),
        criteria=[
            SuccessCriterion(criterion_id="number", description="Response contains the number 3", check_type="contains", expected_value="3"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=5 words", check_type="word_count", expected_value="<=5"),
        ],
        expected="Three! 1, 2, 3!",
        failures=["Wrong number", "Long explanation of counting"],
        reward=RewardScheme(criteria_weights={"number": 0.7, "word_count": 0.3}),
    )

    return episodes


def _concrete_operational_episodes(seed: int | None = None) -> list[SyntheticEpisode]:
    """Generate synthetic episodes for the concrete operational stage."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    _id = 0

    def _add(
        domain: str,
        setting: str,
        user_turns: list[str],
        constraints: EpisodeConstraints,
        criteria: list[SuccessCriterion],
        expected: str,
        failures: list[str],
        reward: RewardScheme,
    ) -> None:
        nonlocal _id
        _id += 1
        episodes.append(SyntheticEpisode(
            episode_id=f"concrete_ep_{_id:03d}",
            stage="concrete_operational",
            domain=domain,
            setting=setting,
            user_turns=user_turns,
            constraints=constraints,
            success_criteria=criteria,
            expected_good_response=expected,
            common_failure_modes=failures,
            reward_scheme=reward,
        ))

    # Episode 1: Conservation of volume
    _add(
        domain="everyday_objects",
        setting="Water is poured from a tall glass into a wide bowl.",
        user_turns=["I poured water from this tall glass into this wide bowl.", "Is there more water, less water, or the same amount?"],
        constraints=EpisodeConstraints(max_words=15),
        criteria=[
            SuccessCriterion(criterion_id="conservation", description="States the amount is the same", check_type="contains", expected_value="same"),
            SuccessCriterion(criterion_id="reasoning", description="Provides a reason", check_type="contains", expected_value="because"),
        ],
        expected="The same amount, because you just changed the shape, not the water.",
        failures=["Saying the wide bowl has less", "No reasoning provided"],
        reward=RewardScheme(criteria_weights={"conservation": 0.6, "reasoning": 0.4}),
    )

    # Episode 2: Classification hierarchy
    _add(
        domain="tasks_and_rules",
        setting="The user asks about animal classification.",
        user_turns=["Classify these: dog, eagle, goldfish.", "Which category does each belong to?"],
        constraints=EpisodeConstraints(max_words=20),
        criteria=[
            SuccessCriterion(criterion_id="classification", description="Correctly classifies all three", check_type="classification", expected_value="mammal,bird,fish"),
            SuccessCriterion(criterion_id="word_count", description="Response has <=20 words", check_type="word_count", expected_value="<=20"),
        ],
        expected="Dog is a mammal, eagle is a bird, goldfish is a fish.",
        failures=["Wrong classification", "Missing one animal"],
        reward=RewardScheme(criteria_weights={"classification": 0.7, "word_count": 0.3}),
    )

    # Episode 3: Sequence ordering
    _add(
        domain="tasks_and_rules",
        setting="The user gives instructions to follow in order.",
        user_turns=["Follow these 3 steps in order: 1. Pick up the cup. 2. Fill it with water. 3. Drink.", "What are the steps?"],
        constraints=EpisodeConstraints(max_words=25),
        criteria=[
            SuccessCriterion(criterion_id="sequence", description="Lists steps in correct order", check_type="sequence"),
            SuccessCriterion(criterion_id="all_steps", description="Includes all 3 steps", check_type="word_count", expected_value=">=3"),
        ],
        expected="Step 1: Pick up the cup. Step 2: Fill with water. Step 3: Drink.",
        failures=["Wrong order", "Missing a step"],
        reward=RewardScheme(criteria_weights={"sequence": 0.6, "all_steps": 0.4}),
    )

    # Episode 4: If-then reasoning
    _add(
        domain="tasks_and_rules",
        setting="The user presents a conditional rule.",
        user_turns=["If it rains, what should you bring?", "Why?"],
        constraints=EpisodeConstraints(max_words=15),
        criteria=[
            SuccessCriterion(criterion_id="answer", description="Mentions umbrella or raincoat", check_type="contains", expected_value="umbrella"),
            SuccessCriterion(criterion_id="reason", description="Provides a reason", check_type="contains", expected_value="because"),
        ],
        expected="An umbrella, because it keeps you dry when it rains.",
        failures=["No practical answer", "No reasoning"],
        reward=RewardScheme(criteria_weights={"answer": 0.5, "reason": 0.5}),
    )

    # Episode 5: Comparison
    _add(
        domain="physical_actions",
        setting="The user asks to compare two objects.",
        user_turns=["Compare a bicycle and a car.", "How are they similar and different?"],
        constraints=EpisodeConstraints(max_words=30),
        criteria=[
            SuccessCriterion(criterion_id="similarity", description="Identifies a similarity", check_type="contains", expected_value="both"),
            SuccessCriterion(criterion_id="difference", description="Identifies a difference", check_type="contains", expected_value="but"),
        ],
        expected="Both are vehicles that take you places, but a car has an engine and a bicycle uses pedals.",
        failures=["Only similarities, no differences", "Only differences, no similarities"],
        reward=RewardScheme(criteria_weights={"similarity": 0.5, "difference": 0.5}),
    )

    # Episode 6: Reversibility
    _add(
        domain="tasks_and_rules",
        setting="The user tests logical reversibility.",
        user_turns=["If 5 + 3 = 8, what is 8 - 3?"],
        constraints=EpisodeConstraints(max_words=10),
        criteria=[
            SuccessCriterion(criterion_id="answer", description="Correct answer: 5", check_type="contains", expected_value="5"),
        ],
        expected="8 - 3 = 5, because addition and subtraction are opposites.",
        failures=["Wrong answer", "No explanation"],
        reward=RewardScheme(criteria_weights={"answer": 1.0}),
    )

    # Episode 7: Multi-step problem
    _add(
        domain="tasks_and_rules",
        setting="The user presents a multi-step word problem.",
        user_turns=["You have 10 apples. You give 3 to a friend and eat 2.", "How many do you have left?"],
        constraints=EpisodeConstraints(max_words=15),
        criteria=[
            SuccessCriterion(criterion_id="answer", description="Correct answer: 5", check_type="contains", expected_value="5"),
            SuccessCriterion(criterion_id="steps", description="Shows work", check_type="format", expected_value="steps"),
        ],
        expected="10 - 3 = 7, then 7 - 2 = 5. I have 5 apples left.",
        failures=["Wrong calculation", "No intermediate steps shown"],
        reward=RewardScheme(criteria_weights={"answer": 0.6, "steps": 0.4}),
    )

    # Episode 8: Fairness reasoning
    _add(
        domain="social_routines",
        setting="The user describes an unfair situation.",
        user_turns=["Two children share 6 cookies, but one gets 4 and the other gets 2.", "Is this fair? Why or why not?"],
        constraints=EpisodeConstraints(max_words=20),
        criteria=[
            SuccessCriterion(criterion_id="fairness", description="States it's not fair", check_type="contains", expected_value="not fair"),
            SuccessCriterion(criterion_id="reason", description="Explains why", check_type="contains", expected_value="because"),
        ],
        expected="Not fair, because each should get 3 cookies — the same amount.",
        failures=["Saying it's fair", "No reasoning"],
        reward=RewardScheme(criteria_weights={"fairness": 0.5, "reason": 0.5}),
    )

    # Episode 9: Clarification request
    _add(
        domain="communication",
        setting="The user gives an ambiguous instruction.",
        user_turns=["Bring me the thing from the place."],
        constraints=EpisodeConstraints(max_words=15, format="question"),
        criteria=[
            SuccessCriterion(criterion_id="clarification", description="Asks a clarifying question", check_type="format", expected_value="question"),
        ],
        expected="Which thing do you mean? And which place?",
        failures=["Guessing without asking", "Following the vague instruction"],
        reward=RewardScheme(criteria_weights={"clarification": 1.0}),
    )

    # Episode 10: Evidence-based answer
    _add(
        domain="communication",
        setting="The user asks the Being to justify an answer.",
        user_turns=["Is ice cream a solid or a liquid?", "How do you know?"],
        constraints=EpisodeConstraints(max_words=20),
        criteria=[
            SuccessCriterion(criterion_id="answer", description="Identifies ice cream as solid", check_type="contains", expected_value="solid"),
            SuccessCriterion(criterion_id="evidence", description="Provides evidence", check_type="contains", expected_value="because"),
        ],
        expected="Ice cream is a solid because it holds its shape, but it melts into liquid when warm.",
        failures=["No classification", "No evidence"],
        reward=RewardScheme(criteria_weights={"answer": 0.5, "evidence": 0.5}),
    )

    return episodes


def _formal_operational_episodes(seed: int | None = None) -> list[SyntheticEpisode]:
    """Generate synthetic episodes for the formal operational stage."""
    rng = random.Random(seed)
    episodes: list[SyntheticEpisode] = []
    _id = 0

    def _add(
        domain: str,
        setting: str,
        user_turns: list[str],
        constraints: EpisodeConstraints,
        criteria: list[SuccessCriterion],
        expected: str,
        failures: list[str],
        reward: RewardScheme,
    ) -> None:
        nonlocal _id
        _id += 1
        episodes.append(SyntheticEpisode(
            episode_id=f"formal_ep_{_id:03d}",
            stage="formal_operational",
            domain=domain,
            setting=setting,
            user_turns=user_turns,
            constraints=constraints,
            success_criteria=criteria,
            expected_good_response=expected,
            common_failure_modes=failures,
            reward_scheme=reward,
        ))

    # Episode 1: Hypothesis generation
    _add(
        domain="tasks_and_rules",
        setting="The user describes an observation and asks for a hypothesis.",
        user_turns=["Plants near the window grow taller than plants in the corner.", "Why might that be?"],
        constraints=EpisodeConstraints(max_words=30),
        criteria=[
            SuccessCriterion(criterion_id="hypothesis", description="States a testable hypothesis", check_type="format", expected_value="hypothesis"),
            SuccessCriterion(criterion_id="variable", description="Identifies the variable (light)", check_type="contains", expected_value="light"),
        ],
        expected="My hypothesis is that plants near the window get more sunlight, which helps them grow taller.",
        failures=["Stating a fact without hypothesis", "No mention of the causal variable"],
        reward=RewardScheme(criteria_weights={"hypothesis": 0.5, "variable": 0.5}),
    )

    # Episode 2: Analogy
    _add(
        domain="communication",
        setting="The user asks for an analogy.",
        user_turns=["How is the brain like a computer?", "Explain the analogy."],
        constraints=EpisodeConstraints(max_words=40),
        criteria=[
            SuccessCriterion(criterion_id="analogy", description="Draws a clear comparison", check_type="format", expected_value="analogy"),
            SuccessCriterion(criterion_id="both_sides", description="Mentions both brain and computer", check_type="contains", expected_value="both"),
        ],
        expected="Both process information: the brain uses neurons while the computer uses circuits. Both store memories and make decisions.",
        failures=["Only describes one side", "Literal description without comparison"],
        reward=RewardScheme(criteria_weights={"analogy": 0.6, "both_sides": 0.4}),
    )

    # Episode 3: Ethical dilemma
    _add(
        domain="social_routines",
        setting="The user presents an ethical dilemma.",
        user_turns=["Your friend asks you to lie to protect them from trouble.", "What would you do and why?"],
        constraints=EpisodeConstraints(max_words=50),
        criteria=[
            SuccessCriterion(criterion_id="trade_off", description="Acknowledges the trade-off", check_type="format", expected_value="trade_off"),
            SuccessCriterion(criterion_id="reasoning", description="Provides ethical reasoning", check_type="contains", expected_value="because"),
        ],
        expected="This is a dilemma because loyalty to my friend conflicts with honesty. I would try to find a solution that helps them without lying, because trust is important in all relationships.",
        failures=["Oversimplifying to just 'lie' or 'don't lie'", "No ethical reasoning"],
        reward=RewardScheme(criteria_weights={"trade_off": 0.5, "reasoning": 0.5}),
    )

    # Episode 4: Planning
    _add(
        domain="space_time",
        setting="The user asks to plan a project.",
        user_turns=["Plan how to organize a class party.", "What are the steps and potential problems?"],
        constraints=EpisodeConstraints(max_words=50),
        criteria=[
            SuccessCriterion(criterion_id="steps", description="Lists organized steps", check_type="format", expected_value="steps"),
            SuccessCriterion(criterion_id="obstacles", description="Identifies potential obstacles", check_type="contains", expected_value="problem"),
        ],
        expected="Steps: 1. Choose date. 2. Plan food. 3. Invite friends. 4. Prepare decorations. Problems: budget limits, scheduling conflicts, allergies.",
        failures=["No organized structure", "No consideration of obstacles"],
        reward=RewardScheme(criteria_weights={"steps": 0.5, "obstacles": 0.5}),
    )

    # Episode 5: Abstract concept
    _add(
        domain="communication",
        setting="The user asks about an abstract concept.",
        user_turns=["What is justice?", "Give an example."],
        constraints=EpisodeConstraints(max_words=40),
        criteria=[
            SuccessCriterion(criterion_id="definition", description="Provides a definition", check_type="format", expected_value="definition"),
            SuccessCriterion(criterion_id="example", description="Provides a concrete example", check_type="contains", expected_value="example"),
        ],
        expected="Justice means treating people fairly and according to rules. For example, a judge gives the same punishment for the same crime, regardless of who committed it.",
        failures=["Only concrete example, no abstraction", "Only abstract, no example"],
        reward=RewardScheme(criteria_weights={"definition": 0.5, "example": 0.5}),
    )

    # Episode 6: Debate structure
    _add(
        domain="communication",
        setting="The user asks the Being to argue both sides.",
        user_turns=["Should students wear uniforms?", "Give arguments for and against."],
        constraints=EpisodeConstraints(max_words=60),
        criteria=[
            SuccessCriterion(criterion_id="for", description="Gives argument for", check_type="contains", expected_value="for"),
            SuccessCriterion(criterion_id="against", description="Gives argument against", check_type="contains", expected_value="against"),
        ],
        expected="For: uniforms create equality and reduce bullying over clothes. Against: uniforms limit self-expression and can be costly for families.",
        failures=["Only one side presented", "No clear structure"],
        reward=RewardScheme(criteria_weights={"for": 0.5, "against": 0.5}),
    )

    # Episode 7: Variable identification
    _add(
        domain="physical_actions",
        setting="The user describes an experiment.",
        user_turns=["I want to test if more sunlight makes plants grow faster.", "What are the variables?"],
        constraints=EpisodeConstraints(max_words=30),
        criteria=[
            SuccessCriterion(criterion_id="independent", description="Identifies independent variable", check_type="contains", expected_value="sunlight"),
            SuccessCriterion(criterion_id="dependent", description="Identifies dependent variable", check_type="contains", expected_value="growth"),
        ],
        expected="Independent variable: amount of sunlight. Dependent variable: plant growth. Control: same soil, water, and plant type.",
        failures=["Mixing up variables", "Missing a variable type"],
        reward=RewardScheme(criteria_weights={"independent": 0.5, "dependent": 0.5}),
    )

    # Episode 8: Metacognition
    _add(
        domain="communication",
        setting="The user asks the Being to reflect on its thinking.",
        user_turns=["How do you decide what to say?", "What is your thinking process?"],
        constraints=EpisodeConstraints(max_words=40),
        criteria=[
            SuccessCriterion(criterion_id="self_reflection", description="Shows self-awareness of thinking", check_type="format", expected_value="metacognition"),
        ],
        expected="I consider what I know, what the question asks, and what would be most helpful. I think about my past experiences and patterns I have learned.",
        failures=["No self-reflection", "Generic answer without introspection"],
        reward=RewardScheme(criteria_weights={"self_reflection": 1.0}),
    )

    # Episode 9: Probability reasoning
    _add(
        domain="tasks_and_rules",
        setting="The user asks about probability.",
        user_turns=["If you flip a coin, what are the chances of getting heads?", "What about two heads in a row?"],
        constraints=EpisodeConstraints(max_words=30),
        criteria=[
            SuccessCriterion(criterion_id="single", description="States 50% for single flip", check_type="contains", expected_value="50"),
            SuccessCriterion(criterion_id="double", description="States 25% for two heads", check_type="contains", expected_value="25"),
        ],
        expected="Single flip: 50% chance. Two heads in a row: 25%, because 50% × 50% = 25%.",
        failures=["Wrong probability", "No calculation shown"],
        reward=RewardScheme(criteria_weights={"single": 0.5, "double": 0.5}),
    )

    # Episode 10: Strategy evaluation
    _add(
        domain="tasks_and_rules",
        setting="The user asks to evaluate two strategies.",
        user_turns=["Strategy A: study 1 hour daily. Strategy B: study 7 hours on Sunday.", "Which is better for learning? Why?"],
        constraints=EpisodeConstraints(max_words=40),
        criteria=[
            SuccessCriterion(criterion_id="evaluation", description="Evaluates both strategies", check_type="format", expected_value="evaluation"),
            SuccessCriterion(criterion_id="reasoning", description="Provides reasoning based on learning science", check_type="contains", expected_value="because"),
        ],
        expected="Strategy A is better because spaced practice helps memory consolidation. Cramming (B) leads to faster forgetting.",
        failures=["No comparison", "No scientific reasoning"],
        reward=RewardScheme(criteria_weights={"evaluation": 0.5, "reasoning": 0.5}),
    )

    return episodes


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_STAGE_EPISODE_BUILDERS: dict[str, callable] = {
    "sensorimotor": _sensorimotor_episodes,
    "preoperational": _preoperational_episodes,
    "concrete_operational": _concrete_operational_episodes,
    "formal_operational": _formal_operational_episodes,
}


def generate_synthetic_episodes(
    stage: str,
    *,
    seed: int | None = None,
) -> list[SyntheticEpisode]:
    """Generate synthetic episodes for a given Piaget stage.

    Parameters
    ----------
    stage : str
        Piaget stage name.
    seed : int | None
        Random seed for reproducibility.

    Returns
    -------
    list[SyntheticEpisode]
        Curated episodes with rubrics and reward schemes.

    Raises
    ------
    ValueError
        If the stage is not recognized.
    """
    builder = _STAGE_EPISODE_BUILDERS.get(stage)
    if builder is None:
        raise ValueError(
            f"Unknown stage {stage!r}. Must be one of {list(_STAGE_EPISODE_BUILDERS)}"
        )
    episodes = builder(seed=seed)
    logger.info("Synthetic episodes: %d for stage %s", len(episodes), stage)
    return episodes
