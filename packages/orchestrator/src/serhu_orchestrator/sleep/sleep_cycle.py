"""Sleep Cycle – Orchestrates the Being's offline processing phases.

Implements a state-machine-like sleep cycle inspired by AWS Step Functions:
0. **Environment Build** – LLM extracts AIXI inputs (one-shot) or
                           NeuralEngine derives them from learned patterns.
                           Produces an ``EnvironmentSpec`` (task description)
                           and a ``WorldModel`` (trained transition model).
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
from serhu_orchestrator.sleep.aixi_environment import EnvironmentSpec, WorldModel
from serhu_orchestrator.sleep.dream_engine import DreamEngine, Hypothesis
from serhu_orchestrator.sleep.neural_engine import NeuralEngine, TrainingResult
from serhu_orchestrator.sleep.value_model import ValueModel

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
    world_model : WorldModel | None
        The trained transition model used for AIXI rollouts,
        versioned separately from the environment spec.
    value_model : ValueModel | None
        Lightweight reward predictor trained on (state, action) → reward
        pairs collected from dream rollouts.  Used by the online planner
        to pre-screen candidates and cut rollout cost.
    """

    facts_extracted: list[str] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    beliefs_added: list[str] = field(default_factory=list)
    traits_before: list[float] = field(default_factory=list)
    traits_after: list[float] = field(default_factory=list)
    cycles_completed: int = 0
    training_result: TrainingResult | None = None
    environment_spec: EnvironmentSpec | None = None
    world_model: WorldModel | None = None
    value_model: ValueModel | None = None


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
        result.world_model = self.dream_engine.world_model

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

        # Phase 4.5: Train ValueModel on (state, action) → reward pairs
        result.value_model = self._train_value_model(
            result.hypotheses, personality_vector
        )

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
        max_cycles: int | None = None,
        cycle_interval_sec: float = 0.1,
        convergence_threshold: float = 1e-4,
        convergence_patience: int = 5,
    ) -> tuple[PersonalityState, SleepResult]:
        """Run AIXI dream cycles until stopped, converged, or max cycles reached.

        By default (max_cycles=None), runs a single cycle. Pass max_cycles=0
        for indefinite AIXI operation (requires external request_stop() call
        or convergence detection).

        Semantization occurs once (first iteration).  Each subsequent
        iteration runs a fresh set of AIXI rollouts and SVD consolidation
        on the progressively refined personality vector, accumulating
        hypotheses and beliefs.

        **Convergence detection**: Monitors personality vector delta between
        cycles.  If the L2 norm of the change drops below
        ``convergence_threshold`` for ``convergence_patience`` consecutive
        cycles, the loop automatically transitions to a "slow mode" with
        exponentially increasing intervals.  Once slow-mode cycles also
        converge, sleep ends gracefully.

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
        cycle_interval_sec : float
            Pause between completed cycles in seconds (default: 0.1).
            Uses an interruptible wait so ``request_stop()`` takes effect promptly.
        convergence_threshold : float
            Minimum personality vector L2 delta to consider a cycle "productive".
        convergence_patience : int
            Number of consecutive below-threshold cycles before entering slow mode.

        Returns
        -------
        tuple[PersonalityState, SleepResult]
            Updated personality state and accumulated sleep metadata.
        """
        import math as _math

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
        result.world_model = self.dream_engine.world_model

        # Phase 1 (once): Train NeuralEngine on episodes
        neural = self.dream_engine.neural_engine
        result.training_result = neural.train(episodes, personality_vector)

        # Phase 2 (once): Semantization – extract facts using learned patterns
        result.facts_extracted = self._semantize(episodes, state)

        # Record initial traits
        result.traits_before = list(self._flatten_traits(state))

        # Default to single cycle for safety (prevent runaway loops)
        if max_cycles is None:
            max_cycles = 1

        # -- Convergence tracking state --
        prev_vector = list(personality_vector)
        stale_streak = 0          # cycles with no meaningful progress
        best_reward = -float("inf")
        total_beliefs = 0
        # Accumulated ValueModel training data across cycles
        vm_pairs: list[tuple[list[float], str]] = []
        vm_targets: list[float] = []
        accumulated_vm: ValueModel | None = None
        # Track hypothesis *semantic fingerprints* (not exact sets)
        # to detect true novelty vs spurious seed variation
        prev_hyp_vocab: set[str] = set()
        # Dream memory: best hypotheses feed back into NeuralEngine
        dream_memory: list[dict] = []
        # NeuralEngine re-training interval (every N cycles)
        _RETRAIN_INTERVAL = 10

        cycle = 0
        while not self._stop_event.is_set():
            cycle += 1
            max_indicator = f"/{max_cycles}" if max_cycles > 0 else "/∞"

            logger.info(f"  [CYCLE {cycle}{max_indicator}] Dream (REM) rollouts...")

            # Dream (REM) – AIXI rollouts with cycle-varied seeds
            personality_vector = self._flatten_traits(state)
            cycle_hypotheses = self.dream_engine.perform_dream_rollouts(
                history=episodes,
                personality_vector=personality_vector,
                num_rollouts=num_rollouts,
                personality_summary=self._build_personality_summary(state),
                cycle_offset=cycle,
            )
            result.hypotheses = cycle_hypotheses

            if self._stop_event.is_set():
                logger.info(f"  [CYCLE {cycle}{max_indicator}] Stop requested after rollouts")
                break

            # Consolidation (NREM) – SVD dream pruning
            consolidated = DreamEngine.dream_pruning(
                personality_vector, target_rank=svd_rank
            )
            result.traits_after = consolidated

            if self._stop_event.is_set():
                logger.info(f"  [CYCLE {cycle}{max_indicator}] Stop requested after consolidation")
                break

            # --- ValueModel: accumulate and train incrementally ---
            for h in cycle_hypotheses:
                if h.action:
                    vm_pairs.append((personality_vector, h.action))
                    vm_targets.append(h.reward)

            if vm_pairs:
                # Only train if there's target variance (otherwise R²=0 guaranteed)
                mean_t = sum(vm_targets) / len(vm_targets)
                target_var = sum((t - mean_t) ** 2 for t in vm_targets) / len(vm_targets)
                if target_var > 1e-8:
                    if accumulated_vm is None:
                        accumulated_vm = ValueModel()
                    metrics = accumulated_vm.fit(vm_pairs, vm_targets)
                    result.value_model = accumulated_vm
                    if cycle == 1 or cycle % 10 == 0:
                        logger.info(
                            "    ValueModel: %d pairs, mse=%.6f, R²=%.4f, v%s",
                            len(vm_pairs), metrics.get("mse", 0.0),
                            metrics.get("r_squared", 0.0), accumulated_vm.version,
                        )
                elif cycle == 1:
                    logger.info(
                        "    ValueModel: skipped — %d pairs with zero variance (σ²=%.2e)",
                        len(vm_pairs), target_var,
                    )

            if self._stop_event.is_set():
                logger.info(f"  [CYCLE {cycle}{max_indicator}] Stop requested after value model")
                break

            # --- Ledger update: apply traits + extract beliefs ---
            state = self._apply_consolidated_traits(state, consolidated)
            new_beliefs = self._extract_beliefs(cycle_hypotheses, state)
            result.beliefs_added.extend(new_beliefs)
            state.core_beliefs.extend(new_beliefs)
            total_beliefs += len(new_beliefs)

            result.cycles_completed = cycle

            # --- Dream memory: feed best hypotheses back as pseudo-episodes ---
            for h in cycle_hypotheses[:3]:
                if h.action and h.reward > 0:
                    dream_memory.append({
                        "role": "dream",
                        "content": h.action.replace("→", " ").replace("_", " "),
                    })

            # --- Progressive NeuralEngine re-training ---
            # Every N cycles, retrain with original episodes + dream memory,
            # so the engine evolves vocabulary and patterns progressively
            if cycle % _RETRAIN_INTERVAL == 0 and dream_memory:
                augmented_episodes = episodes + dream_memory[-50:]  # cap memory
                neural.train(augmented_episodes, personality_vector)
                if cycle % 20 == 0:
                    logger.info(
                        "    NeuralEngine retrained: +%d dream pseudo-episodes → vocab=%d, patterns=%d",
                        len(dream_memory[-50:]),
                        neural.vocabulary_size,
                        neural.pattern_count,
                    )

            # --- Convergence detection (semantic, not exact-set) ---
            new_vector = self._flatten_traits(state)
            delta = _math.sqrt(
                sum((a - b) ** 2 for a, b in zip(new_vector, prev_vector))
            )

            # Best reward tracking
            cycle_best = max((h.reward for h in cycle_hypotheses), default=0.0)
            reward_improved = cycle_best > best_reward + 1e-4
            if reward_improved:
                best_reward = cycle_best

            # Semantic novelty: compare vocabulary tokens across hypotheses,
            # NOT exact action strings (which differ trivially between seeds)
            current_vocab = set()
            for h in cycle_hypotheses:
                for t in h.action.replace("→", " ").replace("_", " ").lower().split():
                    if len(t) > 2:
                        current_vocab.add(t)
            # Jaccard distance from previous cycle's vocabulary
            if prev_hyp_vocab:
                union = len(current_vocab | prev_hyp_vocab) or 1
                jaccard = len(current_vocab & prev_hyp_vocab) / union
                hyp_is_semantically_novel = jaccard < 0.8  # >20% new content
            else:
                hyp_is_semantically_novel = True
            prev_hyp_vocab = current_vocab

            # A cycle is productive if ANY meaningful progress occurred
            is_productive = (
                delta > convergence_threshold
                or reward_improved
                or len(new_beliefs) > 0
                or hyp_is_semantically_novel
            )

            if is_productive:
                stale_streak = 0
            else:
                stale_streak += 1

            # Log progress (every cycle for first 5, then every 10, or on stagnation)
            if cycle <= 5 or cycle % 10 == 0 or stale_streak == convergence_patience:
                logger.info(
                    f"    δ={delta:.6f}, stale={stale_streak}/{convergence_patience}, "
                    f"beliefs={total_beliefs}, best_r={best_reward:.4f}, "
                    f"novel={hyp_is_semantically_novel}, new_beliefs={len(new_beliefs)}"
                )

            prev_vector = new_vector

            # --- Hard convergence: stop when truly stagnant ---
            # No slow mode — if the system is stagnant, more cycles won't help.
            # Instead, stop cleanly and let the next sleep session (with new
            # interactions) bring fresh data for real learning.
            if stale_streak >= convergence_patience:
                logger.info(
                    f"  [CYCLE {cycle}] Converged: no progress for {stale_streak} consecutive "
                    f"cycles (δ={delta:.6f}, beliefs={total_beliefs}, best_r={best_reward:.4f}). "
                    f"Sleep complete — waiting for new interactions."
                )
                break

            if on_cycle is not None:
                on_cycle(cycle, state)

            # Check stop after callback (allows callback to request_stop)
            if self._stop_event.is_set():
                logger.info(f"  [CYCLE {cycle}{max_indicator}] Stop requested externally")
                break

            # Check if max_cycles reached (0 = indefinite)
            if max_cycles > 0 and cycle >= max_cycles:
                logger.info(f"  [CYCLE {cycle}] Max cycles ({max_cycles}) reached, exiting")
                break

            # Inter-cycle cooldown (short, just to yield CPU)
            if cycle_interval_sec > 0.0:
                if self._stop_event.wait(timeout=cycle_interval_sec):
                    logger.info(f"  [CYCLE {cycle}{max_indicator}] Stop requested during inter-cycle wait")
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

        If the neural path returns empty results, supplements with
        rule-based beliefs to ensure every productive dream cycle
        contributes at least some knowledge.

        Accepts hypotheses with any non-negative reward (not just > 0)
        since the AIXI environment may validly assign zero base reward
        to exploratory actions.

        Reference: https://arxiv.org/html/2601.10025v1
        """
        neural = self.dream_engine.neural_engine
        beliefs: list[str] = []

        if neural.is_trained:
            try:
                # Include hypotheses with reward >= 0 (not just > 0)
                # Sort by reward to prioritize high-value hypotheses
                sorted_hyp = sorted(hypotheses, key=lambda h: h.reward, reverse=True)
                hypothesis_texts = [h.action for h in sorted_hyp[:10] if h.action and h.reward >= 0.0]
                if hypothesis_texts:
                    personality_vector = self._flatten_traits(state)
                    beliefs = neural.derive_beliefs(hypothesis_texts, personality_vector)
            except Exception:
                logger.warning(
                    "Neural belief derivation failed, falling back to rule-based",
                    exc_info=True,
                )

        # Supplement with rule-based beliefs if neural produced nothing
        if not beliefs:
            beliefs = self._rule_based_extract_beliefs(hypotheses)

        return beliefs

    @staticmethod
    def _rule_based_extract_beliefs(hypotheses: list[Hypothesis]) -> list[str]:
        """Rule-based belief extraction (original implementation)."""
        beliefs: list[str] = []
        for h in hypotheses[:5]:
            if h.reward >= 0.0 and h.action:
                beliefs.append(f"Learned: {h.action} (confidence={h.reward:.2f})")
        return beliefs[:3]

    @staticmethod
    def _build_personality_summary(state: PersonalityState) -> str:
        """Build a compact personality summary for LLM context."""
        return (
            f"Name: {state.name}, Stage: {state.development.stage}, "
            f"Cognitive age: {state.development.cognitive_age:.1f} months, "
            f"Interactions: {state.development.interaction_count}, "
            f"Language: {state.language}"
        )

    @staticmethod
    def _train_value_model(
        hypotheses: list[Hypothesis],
        personality_vector: list[float],
    ) -> ValueModel | None:
        """Train a ValueModel on (state, action) → reward pairs from dream hypotheses.

        Returns ``None`` if there are no hypotheses or if all rewards are
        identical (zero target variance → R²=0 guaranteed, not worth training).
        """
        pairs: list[tuple[list[float], str]] = []
        targets: list[float] = []
        for h in hypotheses:
            if h.action:
                pairs.append((personality_vector, h.action))
                targets.append(h.reward)

        if not pairs:
            return None

        # Check target variance — skip training if all rewards are identical
        mean_t = sum(targets) / len(targets)
        target_var = sum((t - mean_t) ** 2 for t in targets) / len(targets)
        if target_var < 1e-8:
            logger.info(
                "  Phase 4.5: Skipping ValueModel — %d targets with zero variance (mean=%.4f)",
                len(pairs), mean_t,
            )
            return None

        logger.info(
            "  Phase 4.5: Training ValueModel on %d pairs (σ²=%.6f)", len(pairs), target_var
        )
        vm = ValueModel()
        vm.fit(pairs, targets)
        logger.info(
            "    → ValueModel v%s: mse=%.6f, R²=%.4f",
            vm.version,
            vm.metrics.get("mse", 0.0),
            vm.metrics.get("r_squared", 0.0),
        )
        return vm
