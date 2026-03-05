"""Orchestrator – The Brain.

The top-level controller that ties memory management and personality evolution
together, implementing the MemGPT-like "operating system" for the Being's mind.

Lifecycle phases:
    1. **Wakefulness** – Active interaction via ``process_message()`` or ``chat()``.
    2. **Twilight**    – Consolidation via ``consolidate()``.
    3. **Sleep NREM**  – SVD rank-reduction / dream pruning via ``sleep()``.
    4. **Sleep REM**   – AIXI hypothesis generation via ``sleep()``.

When an ``LLMClient`` is provided (e.g. ``OpenAIClient`` for GPT-5.4),
the Orchestrator can:
- Generate Being responses via ``chat()`` with personality-aware prompts.
- Automatically extract trait deltas from conversations.
- Enhance sleep-cycle semantization and belief derivation.

References:
    - MemGPT: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - Piaget in AI: https://gregrobison.medium.com/active-learning-machines-...
    - AIXI: https://www.alignmentforum.org/w/aixi
    - Dream Pruning: https://pub.towardsai.net/dream-pruning-what-happens-when-ai-models-sleep-3db3c404e24a
    - GPT-5.4: https://openai.com/index/introducing-gpt-5/
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
    llm_client : object | None
        An object satisfying the ``LLMClient`` protocol (e.g. ``OpenAIClient``).
        Enables GPT-5.4-powered chat, trait extraction, and enhanced sleep.
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
        llm_client: object | None = None,
    ) -> None:
        # -- LLM client (optional) -------------------------------------------
        self._llm = llm_client

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

    def chat(
        self,
        user_message: str,
        *,
        auto_traits: bool = True,
        metadata: dict | None = None,
    ) -> tuple[str, ContextWindow]:
        """Full chat turn: process user message → LLM response → trait analysis.

        This is the high-level wakefulness API that uses the LLM to:
        1. Build a persona-aware system prompt.
        2. Assemble the conversation context.
        3. Generate the Being's response via GPT-5.4.
        4. (Optionally) extract personality trait deltas from the exchange.

        Requires an ``llm_client`` to be configured on the Orchestrator.

        Parameters
        ----------
        user_message : str
            The user's input message.
        auto_traits : bool
            If ``True``, uses the LLM to automatically extract trait deltas
            from the conversation turn.
        metadata : dict | None
            Optional metadata for the interaction.

        Returns
        -------
        tuple[str, ContextWindow]
            The Being's response text and the assembled context window.

        Raises
        ------
        RuntimeError
            If no LLM client is configured.
        """
        if self._llm is None:
            raise RuntimeError(
                "chat() requires an LLM client. "
                "Pass llm_client=OpenAIClient(...) to the Orchestrator."
            )

        # 1. Process user message into memory
        context = self._memory_manager.add_interaction("user", user_message, metadata)

        # 2. Build persona-aware system prompt
        system_prompt = build_system_prompt(self._personality)

        # 3. Assemble conversation history from working memory
        messages = [
            {"role": entry.role, "content": entry.content}
            for entry in context.working
        ]

        # 4. Generate Being's response via LLM
        llm_response = self._llm.chat(system_prompt, messages)
        being_response = llm_response.content

        # 5. Store Being's response in memory
        context = self._memory_manager.add_interaction("being", being_response)

        # 6. Optionally extract trait deltas
        trait_deltas = None
        if auto_traits:
            try:
                trait_deltas = self._llm.analyze_traits(
                    system_prompt, user_message, being_response
                )
            except Exception:
                pass

        if trait_deltas:
            self._personality = self._personality_engine.update_traits(
                self._personality, trait_deltas
            )

        return being_response, context

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
        cycle = SleepCycle(dream_engine=dream_engine, llm_client=self._llm)
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
