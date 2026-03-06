"""Memory Manager – Orchestrates the 3-tier MemGPT-like memory system.

Manages the flow of information between:
- WorkingMemory  (RAM)  – immediate conversational context
- ArchivalMemory (Disk) – long-term vector-based semantic retrieval
- RelationalMemory       – structured personality and episode storage

The MemoryManager decides what to promote from working memory to archival
and relational storage when entries are evicted from the FIFO buffer.

References:
    - MemGPT OS analogy: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - MemoryOS: https://arxiv.org/html/2506.06326v1
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field

from serhu_orchestrator.memory.working_memory import WorkingMemory, MemoryEntry
from serhu_orchestrator.memory.archival_memory import ArchivalMemory, ArchivalEntry
from serhu_orchestrator.memory.relational_memory import RelationalMemory

logger = logging.getLogger(__name__)


@dataclass
class ContextWindow:
    """Assembled context for the LLM: working-memory entries + retrieved memories."""

    working: list[MemoryEntry]
    archival_results: list[dict] = field(default_factory=list)
    semantic_facts: list[dict] = field(default_factory=list)


class MemoryManager:
    """Central memory orchestrator.

    Parameters
    ----------
    working : WorkingMemory
        The in-process FIFO buffer.
    archival : ArchivalMemory
        The Qdrant-backed vector store.
    relational : RelationalMemory
        The Supabase-backed relational store.
    being_id : str
        Identifier for the current Being.
    embed_fn : callable | None
        A function ``(text: str) -> list[float]`` that produces embeddings.
        If ``None``, a simple deterministic hash-based pseudo-embedding is used
        (suitable for testing but not for production similarity search).
    """

    def __init__(
        self,
        working: WorkingMemory,
        archival: ArchivalMemory,
        relational: RelationalMemory,
        being_id: str,
        embed_fn: callable | None = None,
    ) -> None:
        self.working = working
        self.archival = archival
        self.relational = relational
        self.being_id = being_id
        self._embed = embed_fn or self._default_embed

    # -- public API ----------------------------------------------------------

    def add_interaction(
        self,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> ContextWindow:
        """Process a new interaction message.

        1. Adds to working memory.
        2. Archives any evicted entries to Qdrant and Supabase.
        3. Retrieves relevant archival memories for the new message.
        4. Returns the assembled context window.
        """
        logger.info(f"💬 add_interaction: {role}='{content[:40]}...'")
        evicted = self.working.add(role, content, metadata)

        # Archive evicted entries
        if evicted:
            logger.info(f"  → Archiving {len(evicted)} evicted entries")
            for entry in evicted:
                self._archive_entry(entry)

        # Log episode to relational store
        self.relational.log_episode(
            being_id=self.being_id,
            role=role,
            content=content,
            metadata=metadata,
        )

        # Retrieve relevant archival context for the new message
        query_vector = self._embed(content)
        archival_results = self.archival.search(query_vector, top_k=3)
        logger.info(f"  → Retrieved {len(archival_results)} archival results")

        # Retrieve semantic facts
        facts = self.relational.get_facts(self.being_id, limit=10)
        logger.info(f"  → Retrieved {len(facts)} semantic facts")

        return ContextWindow(
            working=self.working.get_context(),
            archival_results=archival_results,
            semantic_facts=facts,
        )

    def consolidate(self) -> int:
        """Flush working memory to archival storage.

        This is the "Twilight" phase – called between active conversation
        and sleep cycles. All remaining working-memory entries are promoted
        to long-term storage.

        Returns
        -------
        int
            Number of entries archived.
        """
        entries = self.working.clear()
        for entry in entries:
            self._archive_entry(entry)
        return len(entries)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
    ) -> list[dict]:
        """Semantic search across archival memory.

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
            Matching archival entries with similarity scores.
        """
        vector = self._embed(query)
        return self.archival.search(vector, top_k=top_k, memory_type=memory_type)

    def store_semantic_fact(self, fact: str) -> dict:
        """Store a distilled semantic fact in relational memory.

        This is used during the semantization phase, where recurring
        patterns are extracted from episodes and stored as knowledge.
        """
        return self.relational.store_fact(being_id=self.being_id, fact=fact)

    # -- internal ------------------------------------------------------------

    def _archive_entry(self, entry: MemoryEntry) -> None:
        """Promote a working-memory entry to archival (vector) storage."""
        vector = self._embed(entry.content)
        archival_entry = ArchivalEntry(
            content=entry.content,
            vector=vector,
            memory_type="episodic",
            timestamp=entry.timestamp,
            metadata={
                "role": entry.role,
                **(entry.metadata or {}),
            },
        )
        self.archival.store(archival_entry)

    @staticmethod
    def _default_embed(text: str, dim: int = 384) -> list[float]:
        """Deterministic hash-based pseudo-embedding for testing.

        NOT suitable for real similarity search – use a proper model.
        """
        h = hashlib.sha256(text.encode()).digest()
        raw = []
        idx = 0
        while len(raw) < dim:
            if idx >= len(h):
                h = hashlib.sha256(h).digest()
                idx = 0
            raw.append((h[idx] / 255.0) * 2 - 1)
            idx += 1
        norm = sum(x * x for x in raw) ** 0.5 or 1.0
        return [x / norm for x in raw]
