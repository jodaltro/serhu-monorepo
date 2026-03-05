"""Unit tests for MemoryManager with mocked external services."""

import pytest
from unittest.mock import MagicMock, patch

from serhu_orchestrator.memory.working_memory import WorkingMemory
from serhu_orchestrator.memory.memory_manager import MemoryManager


class TestMemoryManagerUnit:
    """Tests for MemoryManager logic using mocked archival and relational layers."""

    def _make_manager(self, max_entries: int = 5) -> MemoryManager:
        """Create a MemoryManager with mocked external stores."""
        working = WorkingMemory(max_entries=max_entries)

        archival = MagicMock()
        archival.search.return_value = []
        archival.store.return_value = "mock-id"

        relational = MagicMock()
        relational.log_episode.return_value = {}
        relational.get_facts.return_value = []
        relational.store_fact.return_value = {}

        return MemoryManager(
            working=working,
            archival=archival,
            relational=relational,
            being_id="test-being",
        )

    def test_add_interaction_stores_in_working_memory(self):
        mgr = self._make_manager()
        ctx = mgr.add_interaction("user", "Hello!")
        assert len(ctx.working) == 1
        assert ctx.working[0].content == "Hello!"

    def test_add_interaction_logs_episode(self):
        mgr = self._make_manager()
        mgr.add_interaction("user", "Hello!")
        mgr.relational.log_episode.assert_called_once()
        call_kwargs = mgr.relational.log_episode.call_args
        assert call_kwargs.kwargs["content"] == "Hello!"

    def test_evicted_entries_are_archived(self):
        mgr = self._make_manager(max_entries=2)
        mgr.add_interaction("user", "first")
        mgr.add_interaction("user", "second")
        mgr.add_interaction("user", "third")  # evicts "first"
        assert mgr.archival.store.call_count == 1

    def test_consolidate_archives_all(self):
        mgr = self._make_manager()
        mgr.add_interaction("user", "a")
        mgr.add_interaction("user", "b")
        mgr.add_interaction("user", "c")
        archived = mgr.consolidate()
        assert archived == 3
        assert mgr.archival.store.call_count == 3

    def test_retrieve_calls_archival_search(self):
        mgr = self._make_manager()
        mgr.archival.search.return_value = [{"content": "test", "score": 0.9}]
        results = mgr.retrieve("test query")
        assert len(results) == 1
        mgr.archival.search.assert_called_once()

    def test_store_semantic_fact(self):
        mgr = self._make_manager()
        mgr.store_semantic_fact("The user likes sunsets.")
        mgr.relational.store_fact.assert_called_once_with(
            being_id="test-being",
            fact="The user likes sunsets.",
        )

    def test_default_embed_produces_correct_dimension(self):
        vec = MemoryManager._default_embed("hello world")
        assert len(vec) == 384
        # Should be approximately unit-normalized
        norm = sum(x * x for x in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-6

    def test_default_embed_is_deterministic(self):
        v1 = MemoryManager._default_embed("same text")
        v2 = MemoryManager._default_embed("same text")
        assert v1 == v2

    def test_default_embed_differs_for_different_text(self):
        v1 = MemoryManager._default_embed("text A")
        v2 = MemoryManager._default_embed("text B")
        assert v1 != v2
