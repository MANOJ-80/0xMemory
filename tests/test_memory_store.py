"""Tests for MemoryStore."""

import tempfile
from pathlib import Path

import pytest

from oxmemory.core.models import MemoryType
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore


class TestMemoryStore:
    """Tests for MemoryStore."""

    @pytest.fixture
    def initialized_store(self):
        """Create an initialized store in a temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            manager = MarkdownManager(project_dir)
            manager.initialize_brain("Test Project")

            # Also create config
            from oxmemory.core.config import get_default_config, save_config
            config = get_default_config("Test Project")
            save_config(config, project_dir)

            yield MemoryStore(project_dir)

    def test_is_initialized(self, initialized_store):
        """Should detect initialized brain."""
        assert initialized_store.is_initialized()

    def test_add_memory(self, initialized_store):
        """Should add a memory."""
        memory = initialized_store.add(
            content="The API uses JWT",
            memory_type=MemoryType.FACT,
            tags=["api", "auth"],
        )

        assert memory.id.startswith("mem-")
        assert memory.content == "The API uses JWT"
        assert memory.tags == ["api", "auth"]

    def test_get_memory(self, initialized_store):
        """Should get a memory by ID."""
        added = initialized_store.add(content="Test content")

        retrieved = initialized_store.get(added.id)

        assert retrieved is not None
        assert retrieved.content == "Test content"

    def test_get_nonexistent_memory(self, initialized_store):
        """Should return None for nonexistent memory."""
        result = initialized_store.get("nonexistent-id")
        assert result is None

    def test_list_memories(self, initialized_store):
        """Should list memories."""
        initialized_store.add(content="Fact 1", memory_type=MemoryType.FACT)
        initialized_store.add(content="Fact 2", memory_type=MemoryType.FACT)
        initialized_store.add(content="Decision 1", memory_type=MemoryType.DECISION)

        # List all
        all_memories = initialized_store.list_memories()
        assert len(all_memories) == 3

        # List by type
        facts = initialized_store.list_memories(memory_type=MemoryType.FACT)
        assert len(facts) == 2

    def test_delete_memory(self, initialized_store):
        """Should delete a memory."""
        added = initialized_store.add(content="To be deleted")

        result = initialized_store.delete(added.id)

        assert result
        assert initialized_store.get(added.id) is None

    def test_delete_nonexistent_memory(self, initialized_store):
        """Should return False for nonexistent memory."""
        result = initialized_store.delete("nonexistent-id")
        assert not result

    def test_search_keyword(self, initialized_store):
        """Should find memories by keyword."""
        initialized_store.add(content="The API uses JWT authentication")
        initialized_store.add(content="Database is PostgreSQL")
        initialized_store.add(content="Auth middleware handles tokens")

        results = initialized_store.search("authentication")

        assert len(results) >= 1
        assert any("JWT" in m.content for m in results)

    def test_search_by_tag(self, initialized_store):
        """Search should consider tags."""
        initialized_store.add(content="Some content", tags=["api"])
        initialized_store.add(content="Other content", tags=["database"])

        results = initialized_store.search("api")

        assert len(results) >= 1

    def test_search_limit(self, initialized_store):
        """Search should respect limit."""
        for i in range(10):
            initialized_store.add(content=f"Memory about testing {i}")

        results = initialized_store.search("testing", limit=3)

        assert len(results) == 3

    def test_update_memory(self, initialized_store):
        """Should update memory content."""
        added = initialized_store.add(content="Original content")

        updated = initialized_store.update(added.id, "Updated content")

        assert updated is not None
        assert updated.content == "Updated content"

        # Verify persistence
        retrieved = initialized_store.get(added.id)
        assert retrieved.content == "Updated content"

    def test_get_brain_info(self, initialized_store):
        """Should get brain statistics."""
        initialized_store.add(content="Fact", memory_type=MemoryType.FACT)
        initialized_store.add(content="Decision", memory_type=MemoryType.DECISION)

        info = initialized_store.get_brain_info()

        assert info.project_name == "Test Project"
        assert info.facts_count == 1
        assert info.decisions_count == 1
        assert info.total_memories == 2

    def test_get_brain_context(self, initialized_store):
        """Should return brain.md content."""
        context = initialized_store.get_brain_context()

        assert "Test Project" in context or "Project Brain" in context

    def test_get_facts_context(self, initialized_store):
        """Should format facts for context."""
        initialized_store.add(content="API fact", memory_type=MemoryType.FACT, tags=["api"])

        context = initialized_store.get_facts_context()

        assert "API fact" in context
        assert "api" in context
