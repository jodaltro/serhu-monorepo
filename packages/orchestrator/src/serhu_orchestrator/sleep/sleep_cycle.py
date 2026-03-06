"""Sleep Cycle – Orchestrates the Being's offline processing phases.

Implements a state-machine-like sleep cycle inspired by AWS Step Functions:
1. **Semantization**  – Extract semantic facts from recent episodic memory.
2. **Dream (REM)**    – AIXI rollouts to generate and evaluate hypotheses.
3. **Consolidation (NREM)** – SVD dream pruning of personality vectors.
4. **Ledger Update**  – Persist evolved personality and beliefs.

When an ``LLMClient`` is provided (e.g. ``OpenAIClient`` for GPT-5.4),
phases 1 and 4 are enhanced with LLM-powered analysis.  Without an LLM
client the original rule-based logic is used as fallback.

References:
    - MemGPT semantization: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - AIXI: https://www.alignmentforum.org/w/aixi
    - Dream Pruning: https://pub.towardsai.net/dream-pruning-what-happens-when-ai-models-sleep-3db3c404e24a
    - Jungian reflection: https://arxiv.org/html/2601.10025v1
    - GPT-5.4 integration: https://openai.com/index/introducing-gpt-5/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from serhu_orchestrator.personality.types import PersonalityState
from serhu_orchestrator.sleep.dream_engine import DreamEngine, Hypothesis

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
    """

    facts_extracted: list[str] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    beliefs_added: list[str] = field(default_factory=list)
    traits_before: list[float] = field(default_factory=list)
    traits_after: list[float] = field(default_factory=list)


class SleepCycle:
    """Coordinates the Being's offline sleep processing.

    Parameters
    ----------
    dream_engine : DreamEngine
        The engine for dream rollouts and SVD consolidation.
    llm_client : object | None
        An object satisfying the ``LLMClient`` protocol (e.g. ``OpenAIClient``).
        When provided, semantization and belief extraction are enhanced
        with GPT-5.4 analysis.  When ``None``, the original rule-based
        logic is used as fallback.
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
        self._llm = llm_client

    def run(
        self,
        state: PersonalityState,
        episodes: list[dict],
        *,
        num_rollouts: int = 1000,
        svd_rank: int = 8,
    ) -> tuple[PersonalityState, SleepResult]:
        """Execute the full sleep cycle.

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
        result = SleepResult()

        # Phase 1: Semantization – extract facts from episodes
        result.facts_extracted = self._semantize(episodes, state)

        # Phase 2: Dream (REM) – AIXI rollouts
        personality_vector = self._flatten_traits(state)
        result.traits_before = list(personality_vector)

        result.hypotheses = self.dream_engine.perform_dream_rollouts(
            history=episodes,
            personality_vector=personality_vector,
            num_rollouts=num_rollouts,
            personality_summary=self._build_personality_summary(state),
        )

        # Phase 3: Consolidation (NREM) – SVD dream pruning
        consolidated = DreamEngine.dream_pruning(
            personality_vector, target_rank=svd_rank
        )
        result.traits_after = consolidated

        # Phase 4: Ledger update – apply consolidated traits + beliefs
        state = self._apply_consolidated_traits(state, consolidated)
        new_beliefs = self._extract_beliefs(result.hypotheses, state)
        result.beliefs_added = new_beliefs
        state.core_beliefs.extend(new_beliefs)

        return state, result

    # -- internal phases ----------------------------------------------------

    def _semantize(
        self, episodes: list[dict], state: PersonalityState
    ) -> list[str]:
        """Extract semantic facts from episodic memory (Twilight phase).

        When an LLM client is available, uses GPT-5.4 for rich semantic
        extraction.  Otherwise falls back to rule-based keyword analysis.
        """
        if self._llm is not None:
            try:
                personality_summary = self._build_personality_summary(state)
                return self._llm.extract_semantic_facts(episodes, personality_summary)
            except Exception:
                logger.warning(
                    "LLM semantization failed, falling back to rule-based",
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

        When an LLM client is available, uses GPT-5.4 for Jungian
        reflection.  Otherwise falls back to the rule-based mechanism.

        Reference: https://arxiv.org/html/2601.10025v1
        """
        if self._llm is not None:
            try:
                if any(h.reward > 0.0 for h in hypotheses[:10]):
                    hypothesis_texts = [h.action for h in hypotheses[:10] if h.reward > 0.0]
                    personality_summary = self._build_personality_summary(state)
                    return self._llm.derive_beliefs(hypothesis_texts, personality_summary)
            except Exception:
                logger.warning(
                    "LLM belief derivation failed, falling back to rule-based",
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
