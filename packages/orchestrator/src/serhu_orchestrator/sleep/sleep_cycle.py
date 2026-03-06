"""Sleep Cycle – Orchestrates the Being's offline processing phases.

Implements a state-machine-like sleep cycle inspired by AWS Step Functions:
0. **Environment Build** – LLM extracts AIXI inputs (one-shot) or
                           NeuralEngine derives them from learned patterns.
1. **Training**       – NeuralEngine learns from episodic memories
                        (transformer-inspired self-attention and pattern mining).
2. **Semantization**  – Extract semantic facts using learned patterns.
3. **Dream (REM)**    – AIXI rollouts against the built environment.
4. **Consolidation (NREM)** – SVD dream pruning of personality vectors.
5. **Ledger Update**  – Persist evolved personality and beliefs.

The sleep cycle supports two execution modes:

- **Single-shot** (``run``): Executes one complete cycle and returns.
- **Continuous** (``run_continuous``): Runs AIXI rollouts indefinitely,
  as AIXI should be, until ``request_stop()`` is called (e.g. when the
  user wants to interact again).  Each iteration performs a full
  dream cycle, accumulating hypotheses, beliefs, and personality
  refinements across iterations.

The LLM is used **only once at the start** of sleep to extract the
environment inputs (actions, observations, rewards, transitions).
All subsequent AIXI rollouts run autonomously without external calls.

References:
    - MemGPT semantization: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - AIXI: https://www.alignmentforum.org/w/aixi
    - Dream Pruning: https://pub.towardsai.net/dream-pruning-what-happens-when-ai-models-sleep-3db3c404e24a
    - Jungian reflection: https://arxiv.org/html/2601.10025v1
    - Attention Is All You Need: https://arxiv.org/abs/1706.03762
    - Self-supervised learning: https://arxiv.org/abs/2006.08218
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

from serhu_orchestrator.personality.types import PersonalityState
from serhu_orchestrator.sleep.aixi_environment import EnvironmentSpec
from serhu_orchestrator.sleep.dream_engine import DreamEngine, Hypothesis
from serhu_orchestrator.sleep.neural_engine import NeuralEngine, TrainingResult

logger = logging.getLogger(__name__)


@dataclass
class SleepResult:
    """Result of a complete sleep cycle.

    Attributes
    ----------
    facts_extracted : list[str]
        New semantic facts extracted from episodes.
    hypotheses : list[Hypothesis]
        Top dream hypotheses from AIXI rollouts.
    beliefs_added : list[str]
        New beliefs added to the core stack.
    traits_before : list[float]
        Personality vector before consolidation.
    traits_after : list[float]
        Personality vector after SVD pruning.
    cycles_completed : int
        Number of AIXI dream cycles completed (≥1 for single-shot,
        potentially many for continuous mode).
    training_result : TrainingResult | None
        Metrics from the NeuralEngine training phase (vocabulary size,
        pattern count, attention entropy).
    environment_spec : EnvironmentSpec | None
        The AIXI environment specification built at sleep start
        (from LLM or NeuralEngine).
    """

    facts_extracted: list[str] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    beliefs_added: list[str] = field(default_factory=list)
    traits_before: list[float] = field(default_factory=list)
    traits_after: list[float] = field(default_factory=list)
    cycles_completed: int = 0
    training_result: TrainingResult | None = None
    environment_spec: EnvironmentSpec | None = None


class SleepCycle:
    """Coordinates the Being's offline sleep processing.

    Supports two execution modes:

    - **Single-shot** (``run``): One complete environment build →
      training → semantization → dream → consolidation → belief cycle.
    - **Continuous** (``run_continuous``): Loops indefinitely, running
      AIXI rollouts in every iteration, until ``request_stop()`` is
      called.  This models the AIXI ideal of an agent that never stops
      dreaming until external intervention.

    The LLM (if provided) is used **only at the start** of sleep to
    build the AIXI environment specification.  All subsequent rollouts
    run autonomously using the built environment.

    Parameters
    ----------
    dream_engine : DreamEngine
        The engine for dream rollouts and SVD consolidation.
    llm_client : object | None
        LLM client for one-shot environment extraction at sleep start.
        Only used for ``extract_environment_spec()`` — no other LLM
        calls are made during the sleep cycle.
    """

    # Canonical ordering of personality models for vector flattening.
    # HEXACO (24) + TCI-T (16) + TCI-C (13) + Schwartz (19) = 72 dims.
    _TRAIT_MODEL_ATTRS = ("hexaco", "tci_temperament", "tci_character", "schwartz")

    def __init__(
        self,
        dream_engine: DreamEngine | None = None,
        llm_client: object | None = None,
    ) -> None:
        self.dream_engine = dream_engine or DreamEngine()
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        """Signal the continuous sleep loop to stop after the current cycle."""
        self._stop_event.set()

    @property
    def stop_requested(self) -> bool:
        """Whether a stop has been requested."""
        return self._stop_event.is_set()

    def run(
        self,
        state: PersonalityState,
        episodes: list[dict],
        *,
        num_rollouts: int = 1000,
        svd_rank: int = 8,
    ) -> tuple[PersonalityState, SleepResult]:
        """Execute a single full sleep cycle (backward-compatible).

        Parameters
        ----------
        state : PersonalityState
            Current personality state.
        episodes : list[dict]
            Recent episodic memory entries.
        num_rollouts : int
            Number of AIXI dream rollouts.
        svd_rank : int
            Target rank for SVD consolidation.

        Returns
        -------
        tuple[PersonalityState, SleepResult]
            Updated personality state and sleep metadata.
        """
        logger.info(f"💤 SleepCycle.run(): Starting single-shot cycle")
        result = SleepResult()

        # Phase 0: Build AIXI environment (LLM used only here, if available)
        logger.info(f"  Phase 0: Building AIXI environment")
        personality_vector = self._flatten_traits(state)
        personality_summary = self._build_personality_summary(state)
        env_spec = self.dream_engine.build_environment(
            episodes, personality_vector, personality_summary
        )
        result.environment_spec = env_spec

        # Phase 1: Train NeuralEngine on episodes (self-learning)
        logger.info(f"  Phase 1: Training NeuralEngine on {len(episodes)} episodes")
        neural = self.dream_engine.neural_engine
        result.training_result = neural.train(episodes, personality_vector)

        # Phase 2: Semantization – extract facts using learned patterns
        logger.info(f"  Phase 2: Semantizing episodes")
        result.facts_extracted = self._semantize(episodes, state)
        logger.info(f"    → {len(result.facts_extracted)} facts extracted")

        # Phase 3: Dream (REM) – AIXI rollouts against built environment
        logger.info(f"  Phase 3: Dream REM ({num_rollouts} rollouts)")
        result.traits_before = list(personality_vector)

        result.hypotheses = self.dream_engine.perform_dream_rollouts(
            history=episodes,
            personality_vector=personality_vector,
            num_rollouts=num_rollouts,
            personality_summary=self._build_personality_summary(state),
        )
        logger.info(f"    → {len(result.hypotheses)} hypotheses generated")

        # Phase 4: Consolidation (NREM) – SVD dream pruning
        logger.info(f"  Phase 4: Consolidation NREM (SVD rank={svd_rank})")
        consolidated = DreamEngine.dream_pruning(
            personality_vector, target_rank=svd_rank
        )
        result.traits_after = consolidated

        # Phase 5: Ledger update – apply consolidated traits + beliefs
        logger.info(f"  Phase 5: Ledger update")
        state = self._apply_consolidated_traits(state, consolidated)
        new_beliefs = self._extract_beliefs(result.hypotheses, state)
        result.beliefs_added = new_beliefs
        state.core_beliefs.extend(new_beliefs)
        logger.info(f"    → {len(new_beliefs)} beliefs added")

        result.cycles_completed = 1
        logger.info(f"✓ SleepCycle.run() complete: facts={len(result.facts_extracted)}, hypotheses={len(result.hypotheses)}, beliefs={len(result.beliefs_added)}")
        return state, result

    def run_continuous(
        self,
        state: PersonalityState,
        episodes: list[dict],
        *,
        num_rollouts: int = 1000,
        svd_rank: int = 8,
        on_cycle: callable | None = None,
    ) -> tuple[PersonalityState, SleepResult]:
        """Run AIXI dream cycles indefinitely until ``request_stop()`` is called.

        Semantization occurs once (first iteration).  Each subsequent
        iteration runs a fresh set of AIXI rollouts and SVD consolidation
        on the progressively refined personality vector, accumulating
        hypotheses and beliefs.

        Parameters
        ----------
        state : PersonalityState
            Current personality state.
        episodes : list[dict]
            Recent episodic memory entries.
        num_rollouts : int
            Number of AIXI dream rollouts per cycle.
        svd_rank : int
            Target rank for SVD dream pruning.
        on_cycle : callable | None
            Optional callback ``(cycle_number: int, state: PersonalityState) -> None``
            invoked after each completed cycle.

        Returns
        -------
        tuple[PersonalityState, SleepResult]
            Updated personality state and accumulated sleep metadata.
        """
        result = SleepResult()

        # If already stopped (e.g., wake() called before thread started),
        # return immediately.
        if self._stop_event.is_set():
            return state, result

        # Phase 0 (once): Build AIXI environment (LLM used only here)
        personality_vector = self._flatten_traits(state)
        personality_summary = self._build_personality_summary(state)
        env_spec = self.dream_engine.build_environment(
            episodes, personality_vector, personality_summary
        )
        result.environment_spec = env_spec

        # Phase 1 (once): Train NeuralEngine on episodes
        neural = self.dream_engine.neural_engine
        result.training_result = neural.train(episodes, personality_vector)

        # Phase 2 (once): Semantization – extract facts using learned patterns
        result.facts_extracted = self._semantize(episodes, state)

        # Record initial traits
        result.traits_before = list(self._flatten_traits(state))

        cycle = 0
        while not self._stop_event.is_set():
            cycle += 1
            if cycle == 1 or cycle % 500 == 0:
                logger.info("Continuous sleep: dream cycle checkpoint=%d", cycle)

            # Dream (REM) – AIXI rollouts
            personality_vector = self._flatten_traits(state)
            cycle_hypotheses = self.dream_engine.perform_dream_rollouts(
                history=episodes,
                personality_vector=personality_vector,
                num_rollouts=num_rollouts,
                personality_summary=self._build_personality_summary(state),
            )
            result.hypotheses = cycle_hypotheses

            # Consolidation (NREM) – SVD dream pruning
            consolidated = DreamEngine.dream_pruning(
                personality_vector, target_rank=svd_rank
            )
            result.traits_after = consolidated

            # Ledger update
            state = self._apply_consolidated_traits(state, consolidated)
            new_beliefs = self._extract_beliefs(cycle_hypotheses, state)
            result.beliefs_added.extend(new_beliefs)
            state.core_beliefs.extend(new_beliefs)

            result.cycles_completed = cycle

            if on_cycle is not None:
                on_cycle(cycle, state)

            # Check stop after callback (allows callback to request_stop)
            if self._stop_event.is_set():
                break

        logger.info(
            "Continuous sleep ended after %d cycle(s)", result.cycles_completed
        )
        return state, result

    # -- internal phases ----------------------------------------------------

    def _semantize(
        self, episodes: list[dict], state: PersonalityState
    ) -> list[str]:
        """Extract semantic facts from episodic memory (Twilight phase).

        Uses the NeuralEngine's learned patterns to extract semantic facts.
        Falls back to rule-based keyword analysis if neural extraction fails.
        """
        neural = self.dream_engine.neural_engine
        if neural.is_trained:
            try:
                personality_vector = self._flatten_traits(state)
                return neural.extract_semantic_facts(episodes, personality_vector)
            except Exception:
                logger.warning(
                    "Neural semantization failed, falling back to rule-based",
                    exc_info=True,
                )

        return self._rule_based_semantize(episodes)

    @staticmethod
    def _rule_based_semantize(episodes: list[dict]) -> list[str]:
        """Rule-based fact extraction (original implementation)."""
        facts: list[str] = []
        content_freq: dict[str, int] = {}

        for ep in episodes:
            content = ep.get("content", "")
            for word in content.lower().split():
                if len(word) > 4:
                    content_freq[word] = content_freq.get(word, 0) + 1

        for word, count in content_freq.items():
            if count >= 2:
                facts.append(f"The user frequently mentions '{word}'")

        return facts

    @staticmethod
    def _flatten_traits(state: PersonalityState) -> list[float]:
        """Flatten all personality model scores into a single vector.

        Order: HEXACO (24) + TCI-T (16) + TCI-C (13) + Schwartz (19) = 72 dims.
        """
        vector: list[float] = []
        for attr in SleepCycle._TRAIT_MODEL_ATTRS:
            model = getattr(state, attr)
            for field_name in type(model).model_fields:
                vector.append(getattr(model, field_name))
        return vector

    @staticmethod
    def _apply_consolidated_traits(
        state: PersonalityState,
        consolidated: list[float],
    ) -> PersonalityState:
        """Write consolidated trait values back into the personality state."""
        idx = 0
        for attr in SleepCycle._TRAIT_MODEL_ATTRS:
            model = getattr(state, attr)
            for field_name in type(model).model_fields:
                if idx < len(consolidated):
                    setattr(model, field_name, max(0.0, min(1.0, consolidated[idx])))
                    idx += 1
        return state

    def _extract_beliefs(
        self, hypotheses: list[Hypothesis], state: PersonalityState
    ) -> list[str]:
        """Derive new core beliefs from the top dream hypotheses.

        Uses the NeuralEngine's pattern analysis to evaluate which
        hypotheses should become permanent beliefs.  Falls back to
        the rule-based mechanism if neural analysis is unavailable.

        Reference: https://arxiv.org/html/2601.10025v1
        """
        neural = self.dream_engine.neural_engine
        if neural.is_trained:
            try:
                hypothesis_texts = [h.action for h in hypotheses[:10] if h.reward > 0.0]
                if hypothesis_texts:
                    personality_vector = self._flatten_traits(state)
                    return neural.derive_beliefs(hypothesis_texts, personality_vector)
            except Exception:
                logger.warning(
                    "Neural belief derivation failed, falling back to rule-based",
                    exc_info=True,
                )

        return self._rule_based_extract_beliefs(hypotheses)

    @staticmethod
    def _rule_based_extract_beliefs(hypotheses: list[Hypothesis]) -> list[str]:
        """Rule-based belief extraction (original implementation)."""
        beliefs: list[str] = []
        for h in hypotheses[:3]:
            if h.reward > 0.0:
                beliefs.append(f"Learned: {h.action} (confidence={h.reward:.2f})")
        return beliefs

    @staticmethod
    def _build_personality_summary(state: PersonalityState) -> str:
        """Build a compact personality summary for LLM context."""
        return (
            f"Name: {state.name}, Stage: {state.development.stage}, "
            f"Cognitive age: {state.development.cognitive_age:.1f} months, "
            f"Interactions: {state.development.interaction_count}, "
            f"Language: {state.language}"
        )
