"""Online Planner – Real-time AIXI mini-rollouts for action selection.

Turns the offline dream rollouts into an online planning phase that runs
before each chat response.  Instead of only improving the model during
sleep (REM), the Being now *uses* the consolidated WorldModel at chat
time to evaluate candidate responses and pick the best one.

Flow (integrated into ``Orchestrator.chat()``):
    1. Build state from recent context.
    2. Generate K candidate responses (NeuralEngine).
    3. Run short rollouts per candidate using the last WorldModel.
    4. Pick the highest-reward candidate.
    5. After the turn, register real reward for experience.

If no WorldModel is available (the Being has never slept), the planner
is a no-op and ``chat()`` falls back to the existing NeuralEngine path.

References:
    - AIXI: https://www.alignmentforum.org/w/aixi
    - MC-AIXI-CTW: https://www.emergentmind.com/topics/aixi-reinforcement-learning-agent
    - Online planning in POMDPs: https://arxiv.org/abs/1207.4166
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field

from serhu_orchestrator.sleep.aixi_environment import (
    AixiEnvironment,
    EnvironmentSpec,
    WorldModel,
)
from serhu_orchestrator.sleep.neural_engine import NeuralEngine

logger = logging.getLogger(__name__)


@dataclass
class PlanResult:
    """Result of the online planning phase.

    Attributes
    ----------
    chosen_response : str
        The candidate response selected by the planner.
    chosen_action : str
        The AIXI action label that best matched the chosen response.
    expected_reward : float
        Mean discounted reward of the chosen candidate's rollouts.
    candidates_evaluated : int
        Number of candidate responses evaluated.
    rollouts_per_candidate : int
        Number of mini-rollouts executed per candidate.
    all_rewards : list[float]
        Expected reward for each candidate (same order as generation).
    """

    chosen_response: str = ""
    chosen_action: str = ""
    expected_reward: float = 0.0
    candidates_evaluated: int = 0
    rollouts_per_candidate: int = 0
    all_rewards: list[float] = field(default_factory=list)


@dataclass
class Experience:
    """A recorded experience from a real interaction turn.

    Stored after the turn completes so the Being can learn from
    the actual outcome (not just the simulated one).

    Attributes
    ----------
    action : str
        The action/response the Being took.
    observation : str
        What happened next (user's reply or inferred state).
    reward : float
        Real reward computed from the interaction.
    planned_reward : float
        The reward the planner *expected* (for calibration).
    """

    action: str = ""
    observation: str = ""
    reward: float = 0.0
    planned_reward: float = 0.0


class OnlinePlanner:
    """Lightweight real-time planner using the last consolidated WorldModel.

    Generates K candidate responses via the NeuralEngine, evaluates each
    with short AIXI rollouts, and returns the best one.

    Parameters
    ----------
    neural_engine : NeuralEngine
        The Being's self-learned engine (shared with Orchestrator).
    num_candidates : int
        Number of candidate responses to generate (K).
    rollouts_per_candidate : int
        Number of mini-rollouts per candidate.
    horizon : int
        Look-ahead depth for each mini-rollout.
    seed : int | None
        Random seed for reproducibility.
    """

    def __init__(
        self,
        neural_engine: NeuralEngine,
        *,
        num_candidates: int = 5,
        rollouts_per_candidate: int = 10,
        horizon: int = 3,
        seed: int | None = None,
    ) -> None:
        self._neural = neural_engine
        self._num_candidates = num_candidates
        self._rollouts_per_candidate = rollouts_per_candidate
        self._horizon = horizon
        self._rng = random.Random(seed)
        self._seed = seed
        self._experiences: list[Experience] = []

    @property
    def experiences(self) -> list[Experience]:
        """All recorded real-turn experiences."""
        return list(self._experiences)

    # -- Core planning -------------------------------------------------------

    def plan_and_act(
        self,
        context: list[str],
        personality_vector: list[float],
        environment_spec: EnvironmentSpec,
        world_model: WorldModel | None,
        *,
        max_tokens: int = 50,
    ) -> PlanResult:
        """Run the online planning loop: generate candidates → evaluate → pick.

        Parameters
        ----------
        context : list[str]
            Recent conversation context (working memory contents).
        personality_vector : list[float]
            The Being's current personality vector (72 dims).
        environment_spec : EnvironmentSpec
            The AIXI environment specification (from last sleep).
        world_model : WorldModel | None
            The trained transition model (from last sleep).
        max_tokens : int
            Maximum tokens for each candidate response.

        Returns
        -------
        PlanResult
            The chosen response and planning metrics.
        """
        logger.info(
            "🎯 OnlinePlanner: generating %d candidates, %d rollouts each",
            self._num_candidates,
            self._rollouts_per_candidate,
        )

        # Step 1: Generate K candidate responses
        candidates = self._generate_candidates(
            context, personality_vector, max_tokens
        )
        if not candidates:
            logger.warning("  → No candidates generated, returning empty plan")
            return PlanResult()

        logger.info("  → Generated %d candidates", len(candidates))

        # Step 2: Map each candidate to the closest AIXI action
        candidate_actions = [
            self._map_response_to_action(c, environment_spec)
            for c in candidates
        ]

        # Step 3: Evaluate each candidate with mini-rollouts
        candidate_rewards: list[float] = []
        for i, (candidate, action) in enumerate(
            zip(candidates, candidate_actions)
        ):
            avg_reward = self._evaluate_candidate(
                action, personality_vector, environment_spec, world_model
            )
            candidate_rewards.append(avg_reward)
            logger.info(
                "  → Candidate %d: action=%s, avg_reward=%.4f",
                i, action, avg_reward,
            )

        # Step 4: Pick the best candidate
        best_idx = max(range(len(candidate_rewards)), key=lambda i: candidate_rewards[i])
        result = PlanResult(
            chosen_response=candidates[best_idx],
            chosen_action=candidate_actions[best_idx],
            expected_reward=candidate_rewards[best_idx],
            candidates_evaluated=len(candidates),
            rollouts_per_candidate=self._rollouts_per_candidate,
            all_rewards=candidate_rewards,
        )

        logger.info(
            "  ✓ Chosen candidate %d: action=%s, reward=%.4f",
            best_idx, result.chosen_action, result.expected_reward,
        )
        return result

    # -- Experience recording ------------------------------------------------

    def record_experience(
        self,
        action: str,
        observation: str,
        reward: float,
        planned_reward: float = 0.0,
    ) -> Experience:
        """Record the real outcome of a turn for future calibration.

        Parameters
        ----------
        action : str
            The action/response the Being chose.
        observation : str
            What actually happened (e.g. user's next message topic).
        reward : float
            Real reward derived from the interaction.
        planned_reward : float
            The reward the planner expected (for calibration tracking).

        Returns
        -------
        Experience
            The recorded experience.
        """
        exp = Experience(
            action=action,
            observation=observation,
            reward=reward,
            planned_reward=planned_reward,
        )
        self._experiences.append(exp)
        logger.info(
            "📝 Experience recorded: reward=%.4f (planned=%.4f)",
            reward, planned_reward,
        )
        return exp

    # -- Internal: candidate generation --------------------------------------

    def _generate_candidates(
        self,
        context: list[str],
        personality_vector: list[float],
        max_tokens: int,
    ) -> list[str]:
        """Generate K diverse candidate responses from the NeuralEngine.

        Introduces stochastic variation by shuffling pattern ordering
        for each candidate, producing diverse but coherent alternatives.
        """
        candidates: list[str] = []
        seen: set[str] = set()

        for i in range(self._num_candidates):
            # Vary the seed for diversity
            variant_seed = (self._seed or 0) + i + 1
            response = self._neural.generate_response(
                context, personality_vector, max_tokens=max_tokens
            )

            # Add small perturbation by shuffling last tokens
            if response and i > 0:
                tokens = response.split()
                if len(tokens) > 2:
                    rng = random.Random(variant_seed)
                    # Swap two random tokens for diversity
                    a, b = rng.sample(range(len(tokens)), min(2, len(tokens)))
                    tokens[a], tokens[b] = tokens[b], tokens[a]
                    response = " ".join(tokens)

            normalized = response.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                candidates.append(response)

        return candidates

    # -- Internal: action mapping --------------------------------------------

    def _map_response_to_action(
        self, response: str, spec: EnvironmentSpec
    ) -> str:
        """Map a candidate response text to the closest AIXI action.

        Uses token overlap between the response and action labels to find
        the best match.  Falls back to the first action if none match.
        """
        if not spec.actions:
            return "respond"

        response_tokens = set(response.lower().split())

        best_action = spec.actions[0]
        best_score = -1.0

        for action in spec.actions:
            action_tokens = set(action.lower().replace("_", " ").split())
            overlap = len(response_tokens & action_tokens)

            # Boost reward-aligned actions
            reward_boost = 0.0
            for pattern, r in spec.reward_signals.items():
                if pattern.lower() in action.lower():
                    reward_boost += r * 0.1

            score = overlap + reward_boost
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    # -- Internal: candidate evaluation via mini-rollouts --------------------

    def _evaluate_candidate(
        self,
        action: str,
        personality_vector: list[float],
        spec: EnvironmentSpec,
        world_model: WorldModel | None,
    ) -> float:
        """Evaluate a candidate action using short AIXI rollouts.

        Returns the mean discounted reward across rollouts.
        """
        total_reward = 0.0

        # Use a shorter horizon for online planning (bounded cost)
        online_horizon = min(self._horizon, spec.horizon)

        env = AixiEnvironment(
            spec, personality_vector,
            seed=self._seed,
            world_model=world_model,
        )

        for r in range(self._rollouts_per_candidate):
            env.reseed((self._seed or 0) + r)
            env.reset()

            # First step: use the candidate action
            _obs, reward, done, _info = env.step(action)
            rollout_reward = reward

            # Subsequent steps: follow the environment's best action
            for t in range(1, online_horizon):
                if done:
                    break
                # Greedy: pick the action with best reward signal alignment
                next_action = self._greedy_action(
                    spec, env.current_observation, personality_vector
                )
                _obs, reward, done, _info = env.step(next_action)
                rollout_reward += reward * (spec.gamma ** t)

            total_reward += rollout_reward

        return total_reward / max(self._rollouts_per_candidate, 1)

    def _greedy_action(
        self,
        spec: EnvironmentSpec,
        observation: str,
        personality_vector: list[float],
    ) -> str:
        """Pick the greedily best action given the current observation."""
        if not spec.actions:
            return "noop"

        obs_tokens = set(observation.lower().replace("_", " ").split())

        best_action = spec.actions[0]
        best_score = -float("inf")

        for action in spec.actions:
            action_tokens = set(action.lower().replace("_", " ").split())
            overlap = len(action_tokens & obs_tokens)

            reward_boost = 0.0
            for pattern, r in spec.reward_signals.items():
                if pattern.lower() in action.lower():
                    reward_boost += r

            score = overlap * 0.5 + reward_boost
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    # -- Real reward computation ---------------------------------------------

    @staticmethod
    def compute_real_reward(
        user_message: str,
        being_response: str,
        personality_vector: list[float],
        spec: EnvironmentSpec | None = None,
    ) -> float:
        """Compute a real reward from an interaction turn.

        Uses a simple heuristic based on:
        - Response length relative to context (engagement).
        - Token overlap with user message (relevance).
        - Reward signal alignment from the environment spec.

        Parameters
        ----------
        user_message : str
            The user's input that prompted the response.
        being_response : str
            The Being's response text.
        personality_vector : list[float]
            Current personality vector (for curiosity weighting).
        spec : EnvironmentSpec | None
            Optional environment spec for reward signal matching.

        Returns
        -------
        float
            A real reward score (higher is better).
        """
        if not being_response or not being_response.strip():
            return 0.0

        # Engagement: did the Being produce a non-trivial response?
        response_tokens = being_response.lower().split()
        engagement = min(len(response_tokens) / 10.0, 1.0)

        # Relevance: token overlap with user message
        user_tokens = set(user_message.lower().split())
        response_token_set = set(response_tokens)
        overlap = len(user_tokens & response_token_set)
        relevance = overlap / max(len(user_tokens), 1)

        # Environment reward signals (if available)
        signal_reward = 0.0
        if spec:
            combined = f"{being_response} {user_message}".lower()
            for pattern, r in spec.reward_signals.items():
                if pattern.lower() in combined:
                    signal_reward += r

        return engagement * 0.3 + relevance * 0.4 + signal_reward * 0.3
