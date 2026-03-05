"""Unit tests for WorkingMemory."""

import pytest

from serhu_orchestrator.memory.working_memory import WorkingMemory, MemoryEntry


class TestWorkingMemory:
    """Tests for the FIFO working-memory buffer."""

    def test_add_single_entry(self):
        wm = WorkingMemory(max_entries=10)
        evicted = wm.add("user", "Hello, world!")
        assert evicted == []
        assert wm.size == 1

    def test_get_context_returns_entries_in_order(self):
        wm = WorkingMemory(max_entries=10)
        wm.add("user", "first")
        wm.add("being", "second")
        wm.add("user", "third")
        ctx = wm.get_context()
        assert len(ctx) == 3
        assert ctx[0].content == "first"
        assert ctx[1].content == "second"
        assert ctx[2].content == "third"

    def test_eviction_on_overflow(self):
        wm = WorkingMemory(max_entries=3)
        wm.add("user", "a")
        wm.add("user", "b")
        wm.add("user", "c")
        evicted = wm.add("user", "d")
        assert len(evicted) == 1
        assert evicted[0].content == "a"
        assert wm.size == 3
        assert wm.get_context()[0].content == "b"

    def test_multiple_evictions(self):
        wm = WorkingMemory(max_entries=2)
        wm.add("user", "a")
        wm.add("user", "b")
        evicted = wm.add("user", "c")
        assert len(evicted) == 1
        assert evicted[0].content == "a"
        evicted = wm.add("user", "d")
        assert len(evicted) == 1
        assert evicted[0].content == "b"

    def test_search_keyword(self):
        wm = WorkingMemory(max_entries=10)
        wm.add("user", "I love cats")
        wm.add("user", "Dogs are great")
        wm.add("user", "My cat is fluffy")
        results = wm.search("cat")
        assert len(results) == 2
        assert all("cat" in r.content.lower() for r in results)

    def test_search_case_insensitive(self):
        wm = WorkingMemory(max_entries=10)
        wm.add("user", "HELLO World")
        results = wm.search("hello")
        assert len(results) == 1

    def test_clear_returns_all_entries(self):
        wm = WorkingMemory(max_entries=10)
        wm.add("user", "a")
        wm.add("being", "b")
        cleared = wm.clear()
        assert len(cleared) == 2
        assert wm.size == 0

    def test_len_dunder(self):
        wm = WorkingMemory(max_entries=10)
        assert len(wm) == 0
        wm.add("user", "hello")
        assert len(wm) == 1

    def test_metadata_preserved(self):
        wm = WorkingMemory(max_entries=10)
        wm.add("user", "test", metadata={"sentiment": 0.8})
        entry = wm.get_context()[0]
        assert entry.metadata == {"sentiment": 0.8}

    def test_entry_has_timestamp(self):
        wm = WorkingMemory(max_entries=10)
        wm.add("user", "test")
        entry = wm.get_context()[0]
        assert isinstance(entry.timestamp, float)
        assert entry.timestamp > 0
