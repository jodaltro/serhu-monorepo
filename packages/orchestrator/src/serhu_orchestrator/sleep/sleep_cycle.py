"""Sleep Cycle – Orchestrates the Being's offline processing phases.

Implements a state-machine-like sleep cycle inspired by AWS Step Functions:
1. **Semantization**  – Extract semantic facts from recent episodic memory.
2. **Dream (REM)**    – AIXI rollouts to generate and evaluate hypotheses.
3. **Consolidation (NREM)** – SVD dream pruning of personality vectors.
4. **Ledger Update**  – Persist evolved personality and beliefs.

References:
    - MemGPT semantization: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - AIXI: https://www.alignmentforum.org/w/aixi
    - Dream Pruning: https://pub.towardsai.net/dream-pruning-what-happens-when-ai-models-sleep-3db3c404e24a
    - Jungian reflection: https://arxiv.org/html/2601.10025v1
"""

from __future__ import annotations

from dataclasses import dataclass, field

from serhu_orchestrator.personality.types import PersonalityState
from serhu_orchestrator.sleep.dream_engine import DreamEngine, Hypothesis


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
    """

    # Canonical ordering of personality models for vector flattening.
    # HEXACO (24) + TCI-T (16) + TCI-C (13) + Schwartz (19) = 72 dims.
    _TRAIT_MODEL_ATTRS = ("hexaco", "tci_temperament", "tci_character", "schwartz")

    def __init__(self, dream_engine: DreamEngine | None = None) -> None:
        self.dream_engine = dream_engine or DreamEngine()

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
        result.facts_extracted = self._semantize(episodes)

        # Phase 2: Dream (REM) – AIXI rollouts
        personality_vector = self._flatten_traits(state)
        result.traits_before = list(personality_vector)

        result.hypotheses = self.dream_engine.perform_dream_rollouts(
            history=episodes,
            personality_vector=personality_vector,
            num_rollouts=num_rollouts,
        )

        # Phase 3: Consolidation (NREM) – SVD dream pruning
        consolidated = DreamEngine.dream_pruning(
            personality_vector, target_rank=svd_rank
        )
        result.traits_after = consolidated

        # Phase 4: Ledger update – apply consolidated traits + beliefs
        state = self._apply_consolidated_traits(state, consolidated)
        new_beliefs = self._extract_beliefs(result.hypotheses)
        result.beliefs_added = new_beliefs
        state.core_beliefs.extend(new_beliefs)

        return state, result

    # -- internal phases ----------------------------------------------------

    @staticmethod
    def _semantize(episodes: list[dict]) -> list[str]:
        """Extract semantic facts from episodic memory (Twilight phase).

        Identifies recurring patterns and distils them into fact statements.
        In production, this would use an LLM; here we use a rule-based approach.
        """
        facts: list[str] = []
        content_freq: dict[str, int] = {}

        for ep in episodes:
            content = ep.get("content", "")
            # Simple keyword frequency analysis
            for word in content.lower().split():
                if len(word) > 4:
                    content_freq[word] = content_freq.get(word, 0) + 1

        # Extract facts from frequent tokens
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

    @staticmethod
    def _extract_beliefs(hypotheses: list[Hypothesis]) -> list[str]:
        """Derive new core beliefs from the top dream hypotheses.

        Implements the Jungian reflection mechanism: the 'Observer' analyses
        the dream hypotheses to determine which patterns should become
        permanent beliefs vs. transient adaptations.

        Reference: https://arxiv.org/html/2601.10025v1
        """
        beliefs: list[str] = []
        for h in hypotheses[:3]:
            if h.reward > 0.0:
                beliefs.append(f"Learned: {h.action} (confidence={h.reward:.2f})")
        return beliefs
