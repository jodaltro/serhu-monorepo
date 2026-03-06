"""Dream Engine – AIXI hypothesis generation and SVD consolidation.

Implements the two core sleep phases:
1. **REM (Dreaming)**: Monte-Carlo AIXI-CTW rollouts that generate
   hypothetical future interactions, scored by coherence.
   Rollouts run against an ``AixiEnvironment`` (reset/step interface)
   built at sleep start from LLM-extracted inputs or NeuralEngine
   patterns.  The LLM is used *only once* at the beginning of sleep
   to produce the environment specification; all subsequent rollouts
   are autonomous.
2. **NREM (Consolidation)**: SVD rank-reduction applied to personality
   trait vectors, eliminating noise and crystallising intuition.

References:
    - AIXI: https://www.alignmentforum.org/w/aixi
    - MC-AIXI-CTW: https://www.emergentmind.com/topics/aixi-reinforcement-learning-agent
    - Solomonoff induction: https://www.amazon.science/blog/solomonic-learning-large-language-models-and-the-art-of-induction
    - Dream Pruning / SVD: https://pub.towardsai.net/dream-pruning-what-happens-when-ai-models-sleep-3db3c404e24a
    - Dream2Learn: https://arxiv.org/html/2603.01935v1
    - Self-supervised learning: https://arxiv.org/abs/2006.08218
    - Attention Is All You Need: https://arxiv.org/abs/1706.03762
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field


from serhu_orchestrator.sleep.aixi_environment import (
    AixiEnvironment,
    EnvironmentBuilder,
    EnvironmentSpec,
)
from serhu_orchestrator.sleep.neural_engine import NeuralEngine, TrainingResult


logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    """A single dream hypothesis produced by a rollout.

    Attributes
    ----------
    action : str
        A simulated future action/response.
    reward : float
        Coherence score (higher is better).
    complexity : float
        Kolmogorov-like complexity penalty (lower is simpler).
    """

    action: str
    reward: float
    complexity: float = 0.0


class DreamEngine:
    """Generates dream hypotheses via AIXI rollouts and consolidates personality via SVD.

    Rollouts are executed against an ``AixiEnvironment`` that provides
    the standard RL interface (``reset``/``step``).  The environment is
    built once at the start of sleep from:

    - **LLM-extracted inputs** (when an ``llm_client`` is provided):
      The LLM analyzes the Being's episodes and personality to produce
      a rich ``EnvironmentSpec`` with actions, observations, rewards,
      and transition probabilities.  This is the *only* LLM call.
    - **NeuralEngine patterns** (fallback): The Being's self-learned
      vocabulary and n-gram patterns are used to derive the environment.

    Parameters
    ----------
    seed : int | None
        Random seed for reproducible dream rollouts.
    neural_engine : NeuralEngine | None
        Transformer-inspired self-learning engine.  When provided, enables
        pattern-based environment derivation from episodic data.
        A new engine is created automatically if not provided.
    llm_client : object | None
        LLM client for one-shot environment extraction at sleep start.
        Only used for ``extract_environment_spec()`` — no other LLM
        calls are made during rollouts.
    """

    def __init__(
        self,
        seed: int | None = None,
        neural_engine: NeuralEngine | None = None,
        *,
        llm_client: object | None = None,
    ) -> None:
        self._rng = random.Random(seed)
        self._seed = seed
        self._neural = neural_engine or NeuralEngine(seed=seed)
        self._llm_client = llm_client
        self._training_result: TrainingResult | None = None
        self._environment_spec: EnvironmentSpec | None = None

    @property
    def neural_engine(self) -> NeuralEngine:
        """The internal NeuralEngine used for self-learning."""
        return self._neural

    @property
    def last_training_result(self) -> TrainingResult | None:
        """Result of the most recent neural training cycle."""
        return self._training_result

    @property
    def environment_spec(self) -> EnvironmentSpec | None:
        """The environment spec used for the latest rollouts."""
        return self._environment_spec

    # -- Environment building (LLM used only here) --------------------------

    def build_environment(
        self,
        episodes: list[dict],
        personality_vector: list[float],
        personality_summary: str = "",
    ) -> EnvironmentSpec:
        """Build the AIXI environment from LLM or NeuralEngine.

        This is the **only** step that may call the LLM.  If an
        ``llm_client`` is available, it extracts a rich environment
        specification from the episodes and personality.  Otherwise,
        the NeuralEngine's learned patterns are used.

        Parameters
        ----------
        episodes : list[dict]
            Recent episodic memory entries.
        personality_vector : list[float]
            Flattened personality trait vector.
        personality_summary : str
            Compact personality summary for LLM context.

        Returns
        -------
        EnvironmentSpec
            The built environment specification.
        """
        if self._llm_client is not None:
            logger.info("  Building AIXI environment from LLM (one-shot)")
            self._environment_spec = EnvironmentBuilder.from_llm(
                self._llm_client,
                episodes,
                personality_summary,
                personality_vector,
            )
        else:
            logger.info("  Building AIXI environment from NeuralEngine")
            self._environment_spec = EnvironmentBuilder.from_neural_engine(
                self._neural, episodes, personality_vector
            )

        logger.info(
            "  Environment: %d actions, %d observations, horizon=%d, gamma=%.2f",
            len(self._environment_spec.actions),
            len(self._environment_spec.observations),
            self._environment_spec.horizon,
            self._environment_spec.gamma,
        )
        return self._environment_spec

    # -- REM phase: AIXI rollouts -------------------------------------------

    def perform_dream_rollouts(
        self,
        history: list[dict],
        personality_vector: list[float],
        *,
        num_rollouts: int = 1000,
        top_k: int = 10,
        personality_summary: str = "",
    ) -> list[Hypothesis]:
        """Simulate future interactions using MC-AIXI-CTW-inspired rollouts.

        Rollouts are executed against the ``AixiEnvironment``:

        1. **Environment Build** (if not already built): Derives the
           environment spec from LLM or NeuralEngine patterns.
        2. **NeuralEngine Training**: Trains on episodic data for
           action selection guidance.
        3. **AIXI Rollouts**: For each rollout, resets the environment
           and executes a sequence of ``step(action)`` calls, accumulating
           discounted reward.  Action selection uses NeuralEngine patterns
           for exploitation and random exploration for diversity.
        4. **Top-k Selection**: Returns the best hypotheses by reward.

        Parameters
        ----------
        history : list[dict]
            Episodic history entries (role + content).
        personality_vector : list[float]
            Flattened personality trait vector (HEXACO + TCI + Schwartz).
        num_rollouts : int
            Number of Monte-Carlo rollouts.
        top_k : int
            Number of best hypotheses to retain.
        personality_summary : str
            Compact personality summary for environment building.

        Returns
        -------
        list[Hypothesis]
            Top-k hypotheses sorted by reward (descending).
        """
        # Step 1: Ensure environment is built
        if self._environment_spec is None:
            self.build_environment(history, personality_vector, personality_summary)

        spec = self._environment_spec
        assert spec is not None

        # Step 2: Train NeuralEngine for action selection guidance
        try:
            self._training_result = self._neural.train(history, personality_vector)
        except Exception:
            logger.warning(
                "Neural engine training failed, using random action selection",
                exc_info=True,
            )

        # Step 3: Run AIXI rollouts against the environment
        hypotheses: list[Hypothesis] = []
        env = AixiEnvironment(spec, personality_vector, seed=self._seed)

        for i in range(num_rollouts):
            obs = env.reset()
            # Vary the seed per rollout for diversity
            env._rng = random.Random((self._seed or 0) + i)

            total_reward = 0.0
            action_trace: list[str] = []

            for t in range(spec.horizon):
                action = self._select_action(spec, obs, personality_vector, i)
                obs, reward, done, info = env.step(action)
                total_reward += reward * (spec.gamma ** t)
                action_trace.append(action)
                if done:
                    break

            # Complexity: based on trace length and uniqueness
            unique_actions = len(set(action_trace))
            complexity = unique_actions / max(len(spec.actions), 1)

            hypothesis_text = " → ".join(action_trace)
            hypotheses.append(
                Hypothesis(
                    action=hypothesis_text,
                    reward=total_reward,
                    complexity=complexity,
                )
            )

        # Return the top-k hypotheses (Ockham: prefer simple + high-reward)
        hypotheses.sort(key=lambda h: h.reward, reverse=True)
        return hypotheses[:top_k]

    def _select_action(
        self,
        spec: EnvironmentSpec,
        observation: str,
        personality_vector: list[float],
        rollout_idx: int,
    ) -> str:
        """Select an action for one step of an AIXI rollout.

        Uses a mix of NeuralEngine-guided exploitation and random
        exploration, modulated by the Being's openness/curiosity.
        """
        if not spec.actions:
            return "noop"

        # Exploration probability modulated by personality
        openness = (
            personality_vector[20] if len(personality_vector) > 20 else 0.5
        )
        explore_prob = 0.3 + 0.4 * openness

        if self._rng.random() < explore_prob:
            # Explore: random action
            return self._rng.choice(spec.actions)

        # Exploit: prefer actions related to current observation
        best_action = spec.actions[0]
        best_score = -float("inf")

        obs_tokens = set(observation.lower().replace("_", " ").split())

        for action in spec.actions:
            action_tokens = set(action.lower().replace("_", " ").split())
            overlap = len(action_tokens & obs_tokens)

            # Reward signal alignment
            reward_boost = 0.0
            for pattern, r in spec.reward_signals.items():
                if pattern.lower() in action.lower():
                    reward_boost += r

            score = overlap * 0.5 + reward_boost + self._rng.uniform(0, 0.1)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    # -- NREM phase: SVD consolidation --------------------------------------

    @staticmethod
    def dream_pruning(
        trait_vector: list[float],
        target_rank: int = 8,
    ) -> list[float]:
        """Consolidate personality traits via SVD rank-reduction.

        Treats the trait vector as a matrix row and applies a simplified
        SVD decomposition to keep only the ``target_rank`` most significant
        components.  This removes noise from superficial interactions and
        crystallises the Being's core personality traits.

        This is a pure-Python implementation that avoids requiring PyTorch/NumPy
        at import time.  For production use with LoRA weight matrices, replace
        with ``torch.svd``.

        Parameters
        ----------
        trait_vector : list[float]
            Flattened personality vector (e.g. 24 HEXACO + 16 TCI-T + 13 TCI-C + 19 Schwartz = 72 dims).
        target_rank : int
            Number of principal components to retain.

        Returns
        -------
        list[float]
            Consolidated trait vector with noise removed.

        References
        ----------
        Dream Pruning: https://pub.towardsai.net/dream-pruning-what-happens-when-ai-models-sleep-3db3c404e24a
        """
        n = len(trait_vector)
        if n == 0 or target_rank >= n:
            return list(trait_vector)

        # Reshape into a square-ish matrix for SVD approximation.
        # We split the vector into rows of width = target_rank and
        # apply a simplified power-iteration SVD to extract the
        # principal direction, then project back.
        cols = max(target_rank, 1)
        rows = math.ceil(n / cols)
        # Pad to fill a complete matrix
        padded = list(trait_vector) + [0.0] * (rows * cols - n)

        # Build the matrix
        matrix: list[list[float]] = []
        for r in range(rows):
            matrix.append(padded[r * cols : (r + 1) * cols])

        # Simplified rank-reduction via projection:
        # 1. Compute column means (the "DC component")
        col_means = [
            sum(matrix[r][c] for r in range(rows)) / rows for c in range(cols)
        ]

        # 2. Centre the matrix
        centred: list[list[float]] = [
            [matrix[r][c] - col_means[c] for c in range(cols)] for r in range(rows)
        ]

        # 3. Power-iteration to find the top singular vector
        v = [1.0 / math.sqrt(cols)] * cols
        for _ in range(50):  # iterations
            # Matrix-transpose * matrix * v
            u = [sum(centred[r][c] * v[c] for c in range(cols)) for r in range(rows)]
            v_new = [sum(centred[r][c] * u[r] for r in range(rows)) for c in range(cols)]
            norm = math.sqrt(sum(x * x for x in v_new)) or 1.0
            v = [x / norm for x in v_new]

        # 4. Reconstruct using only the DC component + scaled top component
        sigma = math.sqrt(
            sum(
                sum(centred[r][c] * v[c] for c in range(cols)) ** 2
                for r in range(rows)
            )
        )
        u_final = [sum(centred[r][c] * v[c] for c in range(cols)) for r in range(rows)]
        u_norm = math.sqrt(sum(x * x for x in u_final)) or 1.0
        u_final = [x / u_norm for x in u_final]

        reconstructed: list[float] = []
        for r in range(rows):
            for c in range(cols):
                val = col_means[c] + sigma * u_final[r] * v[c]
                reconstructed.append(max(0.0, min(1.0, val)))

        return reconstructed[:n]
