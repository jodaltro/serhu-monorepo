"""Integration tests for ArchivalMemory (Qdrant vector store).

These tests require a real Qdrant instance. Set QDRANT_URL and QDRANT_API_KEY
environment variables (or use a .env file).
"""

import time
import uuid

import pytest

from serhu_orchestrator.memory.archival_memory import ArchivalMemory, ArchivalEntry


@pytest.mark.integration
class TestArchivalMemoryQdrant:
    """Integration tests for Qdrant-backed archival memory."""

    @pytest.fixture(autouse=True)
    def _setup(self, qdrant_url: str, qdrant_api_key: str):
        """Create a test collection and clean up after."""
        self.collection = f"test_archival_{uuid.uuid4().hex[:8]}"
        self.archival = ArchivalMemory(
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=self.collection,
            vector_size=384,
        )
        yield
        try:
            self.archival.delete_collection()
        except Exception:
            pass

    def _make_vector(self, seed: int = 0) -> list[float]:
        """Create a deterministic 384-dim vector for testing."""
        import hashlib

        h = hashlib.sha256(str(seed).encode()).digest()
        raw = []
        idx = 0
        while len(raw) < 384:
            if idx >= len(h):
                h = hashlib.sha256(h).digest()
                idx = 0
            raw.append((h[idx] / 255.0) * 2 - 1)
            idx += 1
        norm = sum(x * x for x in raw) ** 0.5 or 1.0
        return [x / norm for x in raw]

    def test_store_and_count(self):
        """Store an entry and verify the collection count increases."""
        entry = ArchivalEntry(
            content="The user likes the color blue.",
            vector=self._make_vector(1),
            memory_type="episodic",
        )
        entry_id = self.archival.store(entry)
        assert entry_id == entry.entry_id
        # Qdrant is eventually consistent; wait a bit
        time.sleep(1)
        assert self.archival.count() >= 1

    def test_store_and_search(self):
        """Store multiple entries and search by vector similarity."""
        entries = [
            ArchivalEntry(
                content=f"Memory about topic {i}",
                vector=self._make_vector(i),
                memory_type="episodic",
            )
            for i in range(5)
        ]
        for e in entries:
            self.archival.store(e)

        time.sleep(1)

        results = self.archival.search(
            query_vector=self._make_vector(0),
            top_k=3,
        )
        assert len(results) > 0
        # The closest match should be the entry with the same seed
        assert results[0]["content"] == "Memory about topic 0"

    def test_search_with_memory_type_filter(self):
        """Search can be filtered by memory_type."""
        e1 = ArchivalEntry(
            content="Episodic event",
            vector=self._make_vector(10),
            memory_type="episodic",
        )
        e2 = ArchivalEntry(
            content="Semantic fact",
            vector=self._make_vector(11),
            memory_type="semantic",
        )
        self.archival.store(e1)
        self.archival.store(e2)
        time.sleep(1)

        results = self.archival.search(
            query_vector=self._make_vector(11),
            top_k=5,
            memory_type="semantic",
        )
        assert all(r["memory_type"] == "semantic" for r in results)

    def test_delete_collection(self):
        """Deleting the collection removes all data."""
        entry = ArchivalEntry(
            content="Temporary data",
            vector=self._make_vector(99),
        )
        self.archival.store(entry)
        time.sleep(1)

        self.archival.delete_collection()
        # Re-creating should start empty
        self.archival = ArchivalMemory(
            url=self.archival._client._client.rest_uri,
            api_key=self.archival._client._client.rest_uri,
            collection_name=self.collection,
            vector_size=384,
        )
        # The old collection was deleted; accessing it should not find old data
        # (we re-create in __init__)
        assert self.archival.count() == 0
