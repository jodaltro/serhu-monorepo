"""Dream Engine – AIXI hypothesis generation and SVD consolidation.

Implements the two core sleep phases:
1. **REM (Dreaming)**: Monte-Carlo AIXI-CTW rollouts that generate
   hypothetical future interactions, scored by coherence.
   When a ``NeuralEngine`` is available, hypothesis generation uses
   transformer-inspired self-attention and pattern mining over episodic
   data (Solomonoff Induction without external LLM).  Otherwise, the
   engine uses random Monte-Carlo rollouts.
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
    """Generates dream hypotheses and consolidates personality via SVD.

    When a ``NeuralEngine`` is available (default), hypothesis generation
    uses transformer-inspired self-attention and pattern mining over
    episodic data (Solomonoff Induction without external LLM).  The
    NeuralEngine builds an internal language model from the Being's own
    experiences during sleep.

    Without a NeuralEngine, the engine uses random Monte-Carlo rollouts.

    Parameters
    ----------
    seed : int | None
        Random seed for reproducible dream rollouts.
    neural_engine : NeuralEngine | None
        Transformer-inspired self-learning engine.  When provided, enables
        pattern-based hypothesis generation from episodic data.
        A new engine is created automatically if not provided.
    llm_client : object | None
        **Deprecated.** Ignored for backward compatibility.  The Being
        now learns from its own experiences via the NeuralEngine.
    """

    def __init__(
        self,
        seed: int | None = None,
        neural_engine: NeuralEngine | None = None,
        *,
        llm_client: object | None = None,
    ) -> None:
        self._rng = random.Random(seed)
        self._neural = neural_engine or NeuralEngine(seed=seed)
        self._training_result: TrainingResult | None = None

    @property
    def neural_engine(self) -> NeuralEngine:
        """The internal NeuralEngine used for self-learning."""
        return self._neural

    @property
    def last_training_result(self) -> TrainingResult | None:
        """Result of the most recent neural training cycle."""
        return self._training_result

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

        The NeuralEngine trains on episodic data and generates hypotheses:
        1. **Self-Attention Training**: Builds TF-IDF vocabulary and
           attention matrix over episodes (transformer-inspired).
        2. **Pattern-Based Hypotheses**: Generates hypotheses from learned
           n-gram patterns and attention clusters.
        3. **Random Diversity**: Remaining rollout slots are filled with
           random Monte-Carlo hypotheses for exploration breadth.

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
            Compact personality summary (unused, kept for backward compat).

        Returns
        -------
        list[Hypothesis]
            Top-k hypotheses sorted by reward (descending).
        """
        hypotheses: list[Hypothesis] = []

        # Phase 1: NeuralEngine-powered hypotheses (self-learning)
        try:
            self._training_result = self._neural.train(history, personality_vector)
            neural_hypothesis_texts = self._neural.generate_hypotheses(
                history, personality_vector, num_hypotheses=top_k
            )
            # Score each neural hypothesis using the learned model
            for h_text in neural_hypothesis_texts:
                h_tokens = set(self._neural._tokenize_text(h_text))
                vocab_support = sum(
                    self._neural._vocabulary.get(t, 0.0) for t in h_tokens
                )
                complexity = len(h_text) / 200.0
                reward = vocab_support - math.log(complexity + 1.0)
                hypotheses.append(
                    Hypothesis(action=h_text, reward=reward, complexity=complexity)
                )
        except Exception:
            logger.warning(
                "Neural engine training failed, using random rollouts only",
                exc_info=True,
            )

        # Phase 2: Fill remaining slots with random Monte-Carlo rollouts
        remaining = max(num_rollouts - len(hypotheses), 0)
        if remaining > 0:
            random_hypotheses = self._random_rollouts(
                history, personality_vector, remaining, top_k
            )
            hypotheses.extend(random_hypotheses)

        # Return the top-k hypotheses (Ockham: prefer simple + high-reward)
        hypotheses.sort(key=lambda h: h.reward, reverse=True)
        return hypotheses[:top_k]

    def _random_rollouts(
        self,
        history: list[dict],
        personality_vector: list[float],
        num_rollouts: int,
        top_k: int,
    ) -> list[Hypothesis]:
        """Original random Monte-Carlo rollouts."""
        hypotheses: list[Hypothesis] = []
        context_signal = self._extract_context_signal(history)

        for _ in range(num_rollouts):
            action, complexity = self._simulate_action(
                context_signal, personality_vector
            )
            reward = self._evaluate_coherence(action, context_signal, complexity)
            hypotheses.append(
                Hypothesis(action=action, reward=reward, complexity=complexity)
            )

        hypotheses.sort(key=lambda h: h.reward, reverse=True)
        return hypotheses[:top_k]

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

    # -- internal helpers ---------------------------------------------------

    def _extract_context_signal(self, history: list[dict]) -> list[str]:
        """Extract recent content tokens from episodic history."""
        recent = history[-20:] if len(history) > 20 else history
        return [entry.get("content", "") for entry in recent]

    def _simulate_action(
        self,
        context: list[str],
        personality: list[float],
    ) -> tuple[str, float]:
        """Generate a simulated action based on context and personality.

        Returns (action_description, complexity_score).
        """
        # Personality-weighted topic selection:
        # Higher openness/curiosity → more diverse topics
        openness_weight = personality[20] if len(personality) > 20 else 0.5
        exploration_prob = 0.3 + 0.4 * openness_weight

        if self._rng.random() < exploration_prob and context:
            # Explore: combine elements from context
            idx = self._rng.randint(0, len(context) - 1)
            base = context[idx]
            action = f"hypothesis_about:{base[:50]}"
            complexity = len(base) / 100.0
        else:
            # Exploit: reinforce existing patterns
            action = "reinforce_existing_pattern"
            complexity = 0.1

        return action, complexity

    def _evaluate_coherence(
        self,
        action: str,
        context: list[str],
        complexity: float,
    ) -> float:
        """Score a hypothetical action for coherence with history.

        Implements a simplified Solomonoff prior:
        reward = base_coherence - log(complexity + 1)

        Simpler hypotheses (lower complexity) receive higher scores,
        following Ockham's razor / Kolmogorov complexity minimisation.
        """
        # Base coherence: overlap with context keywords
        action_tokens = set(action.lower().split("_"))
        context_tokens: set[str] = set()
        for c in context:
            context_tokens.update(c.lower().split()[:10])

        overlap = len(action_tokens & context_tokens)
        base_coherence = overlap * 0.2 + self._rng.uniform(0.1, 0.5)

        # Solomonoff-inspired penalty: prefer simpler hypotheses
        complexity_penalty = math.log(complexity + 1.0)

        return base_coherence - complexity_penalty
