"""Tests for Markdown storage."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from oxmemory.core.models import Memory, MemoryType
from oxmemory.storage.markdown import (
    MarkdownManager,
    parse_memory_entries,
    serialize_memory_entry,
)


class TestSerializeMemory:
    """Tests for memory serialization."""

    def test_serialize_basic(self):
        """Should serialize a basic memory."""
        memory = Memory(
            id="test-123",
            content="The API uses JWT authentication",
            type=MemoryType.FACT,
            created_at=datetime(2026, 1, 12, 10, 30),
        )

        result = serialize_memory_entry(memory)

        assert "## [2026-01-12 10:30]" in result
        assert "The API uses JWT authentication" in result
        assert "_ID: test-123_" in result
        assert "_Source: manual_" in result
        assert "---" in result

    def test_serialize_with_tags(self):
        """Should include tags in header."""
        memory = Memory(
            id="test-456",
            content="Test content",
            tags=["api", "auth"],
            created_at=datetime(2026, 1, 12, 10, 30),
        )

        result = serialize_memory_entry(memory)

        assert "`api`" in result
        assert "`auth`" in result


class TestParseMemoryEntries:
    """Tests for memory parsing."""

    def test_parse_single_entry(self):
        """Should parse a single memory entry."""
        content = """# Facts

---

## [2026-01-12 10:30] `api` `auth`

The API uses JWT authentication.

_Source: conversation_
_ID: fact-123_

---
"""
        memories = parse_memory_entries(content, MemoryType.FACT)

        assert len(memories) == 1
        assert memories[0].content == "The API uses JWT authentication."
        assert memories[0].tags == ["api", "auth"]
        assert memories[0].id == "fact-123"
        assert memories[0].source == "conversation"

    def test_parse_multiple_entries(self):
        """Should parse multiple memory entries."""
        content = """# Facts

---

## [2026-01-12 10:30]

First fact.

_Source: manual_
_ID: fact-1_

---

## [2026-01-12 11:00] `tag`

Second fact.

_Source: cli_
_ID: fact-2_

---
"""
        memories = parse_memory_entries(content, MemoryType.FACT)

        assert len(memories) == 2
        assert memories[0].content == "First fact."
        assert memories[1].content == "Second fact."
        assert memories[1].tags == ["tag"]

    def test_parse_empty_content(self):
        """Should handle empty content."""
        memories = parse_memory_entries("", MemoryType.FACT)
        assert memories == []

    def test_parse_no_entries(self):
        """Should handle content with no entries."""
        content = "# Just a header\n\nSome text but no entries."
        memories = parse_memory_entries(content, MemoryType.FACT)
        assert memories == []


class TestMarkdownManager:
    """Tests for MarkdownManager."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_initialize_brain(self, temp_project):
        """Should create all brain files."""
        manager = MarkdownManager(temp_project)
        created = manager.initialize_brain("Test Project", "A test project")

        assert "brain" in created
        assert (temp_project / ".0xmemory" / "brain.md").exists()
        assert (temp_project / ".0xmemory" / "memory" / "facts.md").exists()
        assert (temp_project / ".0xmemory" / "memory" / "decisions.md").exists()

    def test_read_write_brain(self, temp_project):
        """Should read and write brain.md."""
        manager = MarkdownManager(temp_project)
        manager.initialize_brain("Test")

        # Read initial content
        content = manager.read_brain()
        assert "Test" in content

        # Write new content
        manager.write_brain("# New Brain\n\nNew content.")

        # Read back
        content = manager.read_brain()
        assert content == "# New Brain\n\nNew content."

    def test_add_and_read_memory(self, temp_project):
        """Should add and read memories."""
        manager = MarkdownManager(temp_project)
        manager.initialize_brain("Test")

        # Add a fact
        memory = Memory(
            content="Test fact content",
            type=MemoryType.FACT,
            tags=["test"],
        )
        manager.add_memory(memory)

        # Read back
        memories = manager.read_memories(MemoryType.FACT)

        assert len(memories) == 1
        assert memories[0].content == "Test fact content"
        assert memories[0].tags == ["test"]

    def test_remove_memory(self, temp_project):
        """Should remove a memory by ID."""
        manager = MarkdownManager(temp_project)
        manager.initialize_brain("Test")

        # Add a memory
        memory = Memory(
            id="test-to-remove",
            content="This will be removed",
            type=MemoryType.FACT,
        )
        manager.add_memory(memory)

        # Verify it exists
        memories = manager.read_memories(MemoryType.FACT)
        assert len(memories) == 1

        # Remove it
        removed = manager.remove_memory("test-to-remove", MemoryType.FACT)
        assert removed

        # Verify it's gone
        memories = manager.read_memories(MemoryType.FACT)
        assert len(memories) == 0

    def test_get_memory_by_id(self, temp_project):
        """Should find memory by ID across types."""
        manager = MarkdownManager(temp_project)
        manager.initialize_brain("Test")

        # Add memories of different types
        fact = Memory(id="fact-1", content="A fact", type=MemoryType.FACT)
        decision = Memory(id="decision-1", content="A decision", type=MemoryType.DECISION)

        manager.add_memory(fact)
        manager.add_memory(decision)

        # Find by ID
        found = manager.get_memory_by_id("decision-1")

        assert found is not None
        assert found.content == "A decision"

    def test_count_memories(self, temp_project):
        """Should count memories by type."""
        manager = MarkdownManager(temp_project)
        manager.initialize_brain("Test")

        # Add some memories
        for i in range(3):
            manager.add_memory(Memory(content=f"Fact {i}", type=MemoryType.FACT))
        for i in range(2):
            manager.add_memory(Memory(content=f"Decision {i}", type=MemoryType.DECISION))

        counts = manager.count_memories()

        assert counts[MemoryType.FACT] == 3
        assert counts[MemoryType.DECISION] == 2
        assert counts[MemoryType.LEARNING] == 0
