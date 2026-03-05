"""Working Memory – In-process FIFO buffer (the "RAM").

Implements the sensory/short-term memory tier of the MemGPT-like architecture.
Holds the most recent interaction context in a bounded buffer, analogous to
the working memory window of a Transformer model.

References:
    - MemGPT: https://informationmatters.org/2025/10/memgpt-engineering-semantic-memory/
    - MemoryOS: https://arxiv.org/html/2506.06326v1
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    """A single entry in working memory."""

    role: str  # "user" | "being" | "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict | None = None


class WorkingMemory:
    """Bounded FIFO buffer for immediate conversational context.

    Acts as the "RAM" in the MemGPT OS analogy.  When the buffer exceeds
    ``max_entries``, the oldest entries are evicted and returned so that the
    MemoryManager can decide whether to archive them.

    Parameters
    ----------
    max_entries : int
        Maximum number of entries to hold (default 50).
    """

    def __init__(self, max_entries: int = 50) -> None:
        self._buffer: list[MemoryEntry] = []
        self.max_entries = max_entries

    # -- public API ----------------------------------------------------------

    def add(self, role: str, content: str, metadata: dict | None = None) -> list[MemoryEntry]:
        """Add a new entry; return any evicted entries.

        Returns
        -------
        list[MemoryEntry]
            Entries that were evicted due to buffer overflow (oldest first).
        """
        entry = MemoryEntry(role=role, content=content, metadata=metadata)
        self._buffer.append(entry)
        evicted: list[MemoryEntry] = []
        while len(self._buffer) > self.max_entries:
            evicted.append(self._buffer.pop(0))
        return evicted

    def get_context(self) -> list[MemoryEntry]:
        """Return the current working-memory window (newest last)."""
        return list(self._buffer)

    def search(self, keyword: str) -> list[MemoryEntry]:
        """Simple keyword search within working memory."""
        keyword_lower = keyword.lower()
        return [e for e in self._buffer if keyword_lower in e.content.lower()]

    def clear(self) -> list[MemoryEntry]:
        """Flush all entries and return them (for archival)."""
        evicted = list(self._buffer)
        self._buffer.clear()
        return evicted

    @property
    def size(self) -> int:
        """Number of entries currently held."""
        return len(self._buffer)

    def __len__(self) -> int:
        return self.size
