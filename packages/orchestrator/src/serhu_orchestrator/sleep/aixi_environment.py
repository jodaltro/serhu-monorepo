"""AIXI Environment – RL-like environment for AIXI dream rollouts.

Provides a proper environment interface for the AIXI approximation,
following the standard RL pattern: ``reset() -> observation`` and
``step(action) -> (observation, reward, done, info)``.

The environment is built from an ``EnvironmentSpec`` that can be
extracted by an LLM at the start of sleep (one-shot) or derived
from the NeuralEngine's learned patterns (fallback).

This decouples the AIXI rollout engine from the data extraction
mechanism, enabling the LLM to provide rich semantic "inputs"
while the AIXI loop itself runs without external API calls.

References:
    - AIXI: https://www.alignmentforum.org/w/aixi
    - MC-AIXI-CTW: https://www.emergentmind.com/topics/aixi-reinforcement-learning-agent
    - OpenAI Gym: https://gymnasium.farama.org/
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field

from serhu_orchestrator.sleep.neural_engine import NeuralEngine

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentSpec:
    """Specification for the AIXI dream environment.

    Extracted once at the start of sleep (by LLM or NeuralEngine)
    and used to build the :class:`AixiEnvironment` for all rollouts.

    Attributes
    ----------
    actions : list[str]
        Finite set of actions the Being can take during rollouts.
        Examples: ``["explore_nature", "ask_about_feelings", "reflect_on_self"]``.
    observations : list[str]
        Vocabulary of possible observations from the environment.
        Examples: ``["user_happy", "user_curious", "silence"]``.
    reward_signals : dict[str, float]
        Mapping from action/observation patterns to base reward values.
        Patterns are matched as substrings against action+observation.
    transition_weights : dict[str, list[tuple[str, float]]]
        For each action, a list of ``(observation, probability)`` pairs
        defining the transition model.
    horizon : int
        Maximum look-ahead steps per rollout episode.
    gamma : float
        Temporal discount factor (0 < gamma ≤ 1).
    """

    actions: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    reward_signals: dict[str, float] = field(default_factory=dict)
    transition_weights: dict[str, list[tuple[str, float]]] = field(
        default_factory=dict
    )
    horizon: int = 10
    gamma: float = 0.95


class AixiEnvironment:
    """RL-like environment for AIXI dream rollouts.

    Implements ``reset()`` and ``step(action)`` following the standard
    Gym interface.  The transition model and reward signals come from
    the ``EnvironmentSpec`` built at sleep start.

    Parameters
    ----------
    spec : EnvironmentSpec
        Environment specification (actions, observations, rewards, etc.).
    personality_vector : list[float]
        The Being's personality vector, used for reward modulation.
    seed : int | None
        Random seed for reproducible rollouts.
    """

    # Named indices into the 72-dim personality vector
    _OPENNESS_INDEX = 20
    _CURIOSITY_INDEX = 24
    _CONSCIENTIOUSNESS_INDEX = 16

    def __init__(
        self,
        spec: EnvironmentSpec,
        personality_vector: list[float],
        seed: int | None = None,
    ) -> None:
        self.spec = spec
        self._personality = personality_vector
        self._rng = random.Random(seed)
        self._current_obs: str = ""
        self._step_count: int = 0

    def reset(self) -> str:
        """Reset the environment and return the initial observation."""
        self._step_count = 0
        if self.spec.observations:
            self._current_obs = self._rng.choice(self.spec.observations)
        else:
            self._current_obs = "initial_state"
        return self._current_obs

    def step(self, action: str) -> tuple[str, float, bool, dict]:
        """Execute one step in the environment.

        Parameters
        ----------
        action : str
            The action to execute (must be from ``spec.actions``).

        Returns
        -------
        tuple[str, float, bool, dict]
            ``(observation, reward, done, info)``
        """
        self._step_count += 1

        # Transition: determine next observation
        observation = self._transition(action)
        self._current_obs = observation

        # Reward: compute from signals + personality modulation
        reward = self._compute_reward(action, observation)

        # Done: when horizon reached
        done = self._step_count >= self.spec.horizon

        info = {
            "step": self._step_count,
            "action": action,
            "observation": observation,
        }
        return observation, reward, done, info

    def _transition(self, action: str) -> str:
        """Determine next observation from transition model."""
        if action in self.spec.transition_weights:
            transitions = self.spec.transition_weights[action]
            if transitions:
                obs_list, weight_list = zip(*transitions)
                return self._rng.choices(list(obs_list), weights=list(weight_list), k=1)[0]

        # Fallback: random observation
        if self.spec.observations:
            return self._rng.choice(self.spec.observations)
        return f"obs_{self._step_count}"

    def _compute_reward(self, action: str, observation: str) -> float:
        """Compute reward from signals and personality modulation."""
        base = 0.0
        combined = f"{action} {observation}".lower()

        for pattern, r in self.spec.reward_signals.items():
            if pattern.lower() in combined:
                base += r

        # Personality modulation
        openness = (
            self._personality[self._OPENNESS_INDEX]
            if len(self._personality) > self._OPENNESS_INDEX
            else 0.5
        )
        curiosity = (
            self._personality[self._CURIOSITY_INDEX]
            if len(self._personality) > self._CURIOSITY_INDEX
            else 0.5
        )

        # Exploration actions rewarded more for curious/open Beings
        explore_keywords = {"explore", "novel", "new", "discover", "ask", "curious"}
        if any(kw in combined for kw in explore_keywords):
            base += (openness + curiosity) * 0.15

        return base

    @property
    def current_observation(self) -> str:
        return self._current_obs


class EnvironmentBuilder:
    """Builds ``EnvironmentSpec`` from LLM analysis or NeuralEngine patterns.

    The LLM path is used when a client is available (one-shot at sleep start).
    The NeuralEngine path is the self-learning fallback.
    """

    @staticmethod
    def from_llm(
        llm_client: object,
        episodes: list[dict],
        personality_summary: str,
        personality_vector: list[float],
    ) -> EnvironmentSpec:
        """Use LLM once to extract AIXI environment inputs.

        Parameters
        ----------
        llm_client : object
            An LLM client with ``extract_environment_spec()`` method.
        episodes : list[dict]
            Recent episodic memory entries.
        personality_summary : str
            Compact personality summary.
        personality_vector : list[float]
            Flattened personality vector.

        Returns
        -------
        EnvironmentSpec
            The extracted environment specification.
        """
        extract_fn = getattr(llm_client, "extract_environment_spec", None)
        if extract_fn is None:
            logger.warning(
                "LLM client does not implement extract_environment_spec(), "
                "falling back to NeuralEngine"
            )
            return EnvironmentBuilder.from_neural_engine(
                NeuralEngine(), episodes, personality_vector
            )

        try:
            raw = extract_fn(episodes, personality_summary)
            return EnvironmentBuilder._parse_llm_spec(raw)
        except Exception:
            logger.warning(
                "LLM environment extraction failed, falling back to NeuralEngine",
                exc_info=True,
            )
            return EnvironmentBuilder.from_neural_engine(
                NeuralEngine(), episodes, personality_vector
            )

    @staticmethod
    def from_neural_engine(
        neural: NeuralEngine,
        episodes: list[dict],
        personality_vector: list[float],
    ) -> EnvironmentSpec:
        """Build environment from NeuralEngine patterns (no LLM needed).

        Derives actions, observations, rewards, and transitions from
        the Being's learned vocabulary and n-gram patterns.

        Parameters
        ----------
        neural : NeuralEngine
            The Being's internal learning engine.
        episodes : list[dict]
            Recent episodic memory entries.
        personality_vector : list[float]
            Flattened personality vector.

        Returns
        -------
        EnvironmentSpec
            The derived environment specification.
        """
        # Ensure engine is trained
        if not neural.is_trained and episodes:
            neural.train(episodes, personality_vector)

        # Derive actions from top vocabulary tokens and patterns
        actions = EnvironmentBuilder._derive_actions(neural, episodes)

        # Derive observations from episode content patterns
        observations = EnvironmentBuilder._derive_observations(neural, episodes)

        # Derive reward signals from personality-weighted patterns
        reward_signals = EnvironmentBuilder._derive_rewards(
            neural, personality_vector
        )

        # Build transition model from co-occurrence patterns
        transition_weights = EnvironmentBuilder._derive_transitions(
            actions, observations, neural
        )

        # Horizon based on episode count (more data → longer horizon)
        horizon = min(max(len(episodes), 5), 20)

        return EnvironmentSpec(
            actions=actions,
            observations=observations,
            reward_signals=reward_signals,
            transition_weights=transition_weights,
            horizon=horizon,
            gamma=0.95,
        )

    # -- internal helpers ---------------------------------------------------

    @staticmethod
    def _derive_actions(neural: NeuralEngine, episodes: list[dict]) -> list[str]:
        """Derive action set from learned patterns and episode themes."""
        actions: list[str] = []

        # Base actions available to any Being
        base_actions = [
            "respond_empathically",
            "ask_question",
            "explore_topic",
            "reflect_on_self",
            "reinforce_pattern",
        ]
        actions.extend(base_actions)

        # Pattern-derived actions (from top vocabulary tokens)
        if neural.is_trained:
            top_tokens = sorted(
                neural._vocabulary.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
            for token, _weight in top_tokens:
                if len(token) > 2:
                    actions.append(f"discuss_{token}")

        # Episode-derived actions (from user topics)
        topic_tokens: set[str] = set()
        for ep in episodes[-20:]:
            content = ep.get("content", "")
            for t in neural.tokenize(content) if neural.is_trained else []:
                if len(t) > 3:
                    topic_tokens.add(t)

        for t in list(topic_tokens)[:5]:
            action = f"explore_{t}"
            if action not in actions:
                actions.append(action)

        return actions

    @staticmethod
    def _derive_observations(
        neural: NeuralEngine, episodes: list[dict]
    ) -> list[str]:
        """Derive observation vocabulary from episodes."""
        observations = [
            "user_engaged",
            "user_curious",
            "user_happy",
            "user_reflective",
            "user_teaching",
            "silence",
        ]

        # Add episode-derived observations
        if neural.is_trained:
            top_tokens = sorted(
                neural._vocabulary.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:8]
            for token, _weight in top_tokens:
                if len(token) > 2:
                    observations.append(f"topic_{token}")

        return observations

    @staticmethod
    def _derive_rewards(
        neural: NeuralEngine, personality_vector: list[float]
    ) -> dict[str, float]:
        """Derive reward signals from personality and patterns."""
        openness = (
            personality_vector[20]
            if len(personality_vector) > 20
            else 0.5
        )
        conscientiousness = (
            personality_vector[16]
            if len(personality_vector) > 16
            else 0.5
        )
        curiosity = (
            personality_vector[24]
            if len(personality_vector) > 24
            else 0.5
        )

        rewards: dict[str, float] = {
            # Base rewards for fundamental interactions
            "respond_empathically": 0.3,
            "ask_question": 0.2 + curiosity * 0.2,
            "explore": 0.1 + openness * 0.3,
            "reflect": 0.2 + conscientiousness * 0.1,
            "reinforce_pattern": 0.15,
            # Observation-based rewards
            "user_engaged": 0.3,
            "user_happy": 0.4,
            "user_curious": 0.25,
            "user_teaching": 0.35,
            "silence": -0.1,
        }

        # Pattern-derived rewards (topics the user cares about)
        if neural.is_trained:
            top_tokens = sorted(
                neural._vocabulary.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]
            for token, weight in top_tokens:
                rewards[token] = min(weight * 2.0, 0.5)

        return rewards

    @staticmethod
    def _derive_transitions(
        actions: list[str],
        observations: list[str],
        neural: NeuralEngine,
    ) -> dict[str, list[tuple[str, float]]]:
        """Build transition model from action-observation associations."""
        if not observations:
            return {}

        transitions: dict[str, list[tuple[str, float]]] = {}
        n_obs = len(observations)

        for action in actions:
            weights: list[tuple[str, float]] = []
            for obs in observations:
                # Base uniform weight
                w = 1.0 / n_obs

                # Boost semantically related transitions
                action_lower = action.lower()
                obs_lower = obs.lower()

                if "empathic" in action_lower and "happy" in obs_lower:
                    w += 0.3
                elif "question" in action_lower and "curious" in obs_lower:
                    w += 0.3
                elif "explore" in action_lower and "engaged" in obs_lower:
                    w += 0.2
                elif "reflect" in action_lower and "reflective" in obs_lower:
                    w += 0.3
                elif "reinforce" in action_lower and "teaching" in obs_lower:
                    w += 0.2

                # Token overlap boost
                action_tokens = set(action_lower.replace("_", " ").split())
                obs_tokens = set(obs_lower.replace("_", " ").split())
                overlap = len(action_tokens & obs_tokens)
                if overlap > 0:
                    w += 0.15 * overlap

                weights.append((obs, w))

            transitions[action] = weights

        return transitions

    @staticmethod
    def _parse_llm_spec(raw: dict) -> EnvironmentSpec:
        """Parse LLM-returned dict into EnvironmentSpec."""
        if not isinstance(raw, dict):
            return EnvironmentSpec()

        actions = raw.get("actions", [])
        if not isinstance(actions, list):
            actions = []
        actions = [str(a) for a in actions if a]

        observations = raw.get("observations", [])
        if not isinstance(observations, list):
            observations = []
        observations = [str(o) for o in observations if o]

        reward_signals: dict[str, float] = {}
        raw_rewards = raw.get("reward_signals", {})
        if isinstance(raw_rewards, dict):
            for k, v in raw_rewards.items():
                try:
                    reward_signals[str(k)] = float(v)
                except (ValueError, TypeError):
                    pass

        transition_weights: dict[str, list[tuple[str, float]]] = {}
        raw_transitions = raw.get("transition_weights", {})
        if isinstance(raw_transitions, dict):
            for action, trans_list in raw_transitions.items():
                if isinstance(trans_list, list):
                    parsed: list[tuple[str, float]] = []
                    for item in trans_list:
                        if isinstance(item, (list, tuple)) and len(item) >= 2:
                            try:
                                parsed.append((str(item[0]), float(item[1])))
                            except (ValueError, TypeError):
                                pass
                    if parsed:
                        transition_weights[str(action)] = parsed

        horizon = int(raw.get("horizon", 10))
        gamma = float(raw.get("gamma", 0.95))
        horizon = max(1, min(horizon, 50))
        gamma = max(0.0, min(gamma, 1.0))

        return EnvironmentSpec(
            actions=actions,
            observations=observations,
            reward_signals=reward_signals,
            transition_weights=transition_weights,
            horizon=horizon,
            gamma=gamma,
        )
