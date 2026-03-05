"""Orchestrator – The Brain.

The top-level controller that ties memory management and personality evolution
together, implementing the MemGPT-like "operating system" for the Being's mind.

Lifecycle phases:
    1. **Wakefulness** – Active interaction via ``process_message()``.
    2. **Twilight**    – Consolidation via ``consolidate()``.
    3. **Sleep NREM**  – SVD rank-reduction / dream pruning via ``sleep()``.
    4. **Sleep REM**   – AIXI hypothesis generation via ``sleep()``.

References:
    - MemGPT: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - Piaget in AI: https://gregrobison.medium.com/active-learning-machines-...
    - AIXI: https://www.alignmentforum.org/w/aixi
    - Dream Pruning: https://pub.towardsai.net/dream-pruning-what-happens-when-ai-models-sleep-3db3c404e24a
"""

from __future__ import annotations

from serhu_orchestrator.memory.working_memory import WorkingMemory
from serhu_orchestrator.memory.archival_memory import ArchivalMemory
from serhu_orchestrator.memory.relational_memory import RelationalMemory
from serhu_orchestrator.memory.memory_manager import MemoryManager, ContextWindow
from serhu_orchestrator.personality.personality_engine import PersonalityEngine
from serhu_orchestrator.personality.prompt_builder import build_system_prompt
from serhu_orchestrator.personality.types import PersonalityState
from serhu_orchestrator.sleep.dream_engine import DreamEngine
from serhu_orchestrator.sleep.sleep_cycle import SleepCycle, SleepResult


class Orchestrator:
    """The Brain – central orchestrator for a synthetic Being.

    Parameters
    ----------
    qdrant_url : str
        Qdrant cluster endpoint.
    qdrant_api_key : str
        Qdrant API key.
    supabase_url : str
        Supabase project URL.
    supabase_key : str
        Supabase anon/service key.
    being_id : str | None
        Existing Being to load.  If ``None``, a new Being is created.
    being_name : str
        Name for a new Being (ignored if ``being_id`` is given).
    language : str
        Default language code (e.g., 'en', 'pt', 'es', 'fr').
        Only applies when creating a new Being; ignored if loading an existing one.
    working_memory_size : int
        Max entries in the working-memory FIFO buffer.
    collection_name : str
        Qdrant collection name.
    embed_fn : callable | None
        Embedding function ``(text) -> list[float]``.
    """

    def __init__(
        self,
        *,
        qdrant_url: str,
        qdrant_api_key: str,
        supabase_url: str,
        supabase_key: str,
        being_id: str | None = None,
        being_name: str = "",
        language: str = "en",
        working_memory_size: int = 50,
        collection_name: str = "serhu_archival",
        embed_fn: callable | None = None,
    ) -> None:
        # -- memory tiers ----------------------------------------------------
        self._working = WorkingMemory(max_entries=working_memory_size)
        self._archival = ArchivalMemory(
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=collection_name,
            vector_size=384,
        )
        self._relational = RelationalMemory(url=supabase_url, key=supabase_key)

        # -- personality engine ----------------------------------------------
        self._personality_engine = PersonalityEngine(relational=self._relational)

        if being_id:
            personality = self._personality_engine.load_being(being_id)
            if personality is None:
                raise ValueError(f"Being {being_id!r} not found in relational memory")
            self._personality = personality
        else:
            self._personality = self._personality_engine.create_being(
                name=being_name, language=language
            )

        # -- memory manager --------------------------------------------------
        self._memory_manager = MemoryManager(
            working=self._working,
            archival=self._archival,
            relational=self._relational,
            being_id=self._personality.being_id,
            embed_fn=embed_fn,
        )

    # -- properties ----------------------------------------------------------

    @property
    def being_id(self) -> str:
        return self._personality.being_id

    @property
    def personality(self) -> PersonalityState:
        return self._personality

    # -- wakefulness phase ---------------------------------------------------

    def process_message(
        self,
        role: str,
        content: str,
        metadata: dict | None = None,
        trait_deltas: dict[str, dict[str, float]] | None = None,
    ) -> ContextWindow:
        """Process an incoming message during the wakefulness phase.

        1. Adds the message to the memory pipeline.
        2. Optionally updates personality traits.
        3. Returns the assembled context window for LLM consumption.

        Parameters
        ----------
        role : str
            Speaker role (user | being | system).
        content : str
            Message text.
        metadata : dict | None
            Optional metadata (sentiment scores, topic tags, etc.).
        trait_deltas : dict | None
            Optional personality trait updates (see PersonalityEngine.update_traits).

        Returns
        -------
        ContextWindow
            The assembled context for the LLM.
        """
        context = self._memory_manager.add_interaction(role, content, metadata)

        if trait_deltas:
            self._personality = self._personality_engine.update_traits(
                self._personality, trait_deltas
            )

        return context

    # -- twilight phase ------------------------------------------------------

    def consolidate(self) -> int:
        """Consolidate working memory to long-term storage.

        Called at the end of a conversation session ("Twilight" phase).

        Returns
        -------
        int
            Number of entries archived.
        """
        return self._memory_manager.consolidate()

    # -- retrieval -----------------------------------------------------------

    def recall(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[dict]:
        """Recall memories relevant to a query.

        Parameters
        ----------
        query : str
            Natural-language query.
        top_k : int
            Number of results.
        memory_type : str | None
            Optional filter (episodic | semantic | causal).

        Returns
        -------
        list[dict]
            Matching memories with similarity scores.
        """
        return self._memory_manager.retrieve(query, top_k=top_k, memory_type=memory_type)

    def learn_fact(self, fact: str) -> dict:
        """Store a semantic fact (semantization phase).

        Parameters
        ----------
        fact : str
            Distilled knowledge statement.

        Returns
        -------
        dict
            The stored fact row.
        """
        return self._memory_manager.store_semantic_fact(fact)

    # -- sleep phase ---------------------------------------------------------

    def sleep(
        self,
        *,
        num_rollouts: int = 1000,
        svd_rank: int = 8,
        seed: int | None = None,
    ) -> SleepResult:
        """Execute the full sleep cycle (NREM + REM).

        Orchestrates:
        1. Retrieve recent episodes from relational memory.
        2. Run the SleepCycle: semantization → AIXI dreams → SVD consolidation.
        3. Store extracted facts and persist the updated personality.

        Parameters
        ----------
        num_rollouts : int
            Number of AIXI dream rollouts.
        svd_rank : int
            Target rank for SVD dream pruning.
        seed : int | None
            Random seed for reproducible dreams.

        Returns
        -------
        SleepResult
            Metadata about the sleep cycle.
        """
        # Retrieve recent episodes
        episodes = self._relational.get_episodes(self._personality.being_id, limit=100)

        # Run the sleep cycle
        dream_engine = DreamEngine(seed=seed)
        cycle = SleepCycle(dream_engine=dream_engine)
        self._personality, result = cycle.run(
            self._personality,
            episodes,
            num_rollouts=num_rollouts,
            svd_rank=svd_rank,
        )

        # Store extracted facts in relational memory
        for fact in result.facts_extracted:
            self._memory_manager.store_semantic_fact(fact)

        # Persist the updated personality
        self._personality_engine._persist(self._personality)

        return result

    # -- prompt building -----------------------------------------------------

    def build_prompt(self) -> str:
        """Build a structured system prompt from the current personality ledger.

        Returns
        -------
        str
            A system prompt with persona tags, cognitive constraints,
            and Erikson conflict framing for LLM consumption.
        """
        return build_system_prompt(self._personality)

    # -- cleanup (for testing) -----------------------------------------------

    def cleanup_archival(self) -> None:
        """Delete the Qdrant collection (for test cleanup)."""
        self._archival.delete_collection()
