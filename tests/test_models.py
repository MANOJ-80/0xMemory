"""Tests for core models."""

from datetime import datetime

import pytest

from oxmemory.core.models import (
    BrainInfo,
    Config,
    Memory,
    MemoryType,
    ProjectConfig,
)


class TestMemory:
    """Tests for the Memory model."""

    def test_memory_creation_defaults(self):
        """Memory should have sensible defaults."""
        memory = Memory(content="Test content")

        assert memory.content == "Test content"
        assert memory.type == MemoryType.FACT
        assert memory.tags == []
        assert memory.source == "manual"
        assert memory.salience == 0.5
        assert memory.id.startswith("mem-")
        assert isinstance(memory.created_at, datetime)

    def test_memory_creation_full(self):
        """Memory should accept all fields."""
        memory = Memory(
            content="The API uses JWT",
            type=MemoryType.DECISION,
            tags=["api", "auth"],
            source="conversation",
            salience=0.8,
        )

        assert memory.content == "The API uses JWT"
        assert memory.type == MemoryType.DECISION
        assert memory.tags == ["api", "auth"]
        assert memory.source == "conversation"
        assert memory.salience == 0.8

    def test_memory_touch(self):
        """Touch should update accessed_at."""
        memory = Memory(content="Test")
        original_accessed = memory.accessed_at

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        memory.touch()

        assert memory.accessed_at > original_accessed

    def test_memory_update_content(self):
        """Update content should update content and updated_at."""
        memory = Memory(content="Original")
        original_updated = memory.updated_at

        import time
        time.sleep(0.01)

        memory.update_content("Updated content")

        assert memory.content == "Updated content"
        assert memory.updated_at > original_updated

    def test_memory_salience_validation(self):
        """Salience must be between 0 and 1."""
        with pytest.raises(ValueError):
            Memory(content="Test", salience=1.5)

        with pytest.raises(ValueError):
            Memory(content="Test", salience=-0.1)


class TestMemoryType:
    """Tests for MemoryType enum."""

    def test_memory_types(self):
        """All memory types should exist."""
        assert MemoryType.FACT.value == "fact"
        assert MemoryType.DECISION.value == "decision"
        assert MemoryType.LEARNING.value == "learning"
        assert MemoryType.PREFERENCE.value == "preference"

    def test_memory_type_from_string(self):
        """Should create from string."""
        assert MemoryType("fact") == MemoryType.FACT
        assert MemoryType("decision") == MemoryType.DECISION


class TestConfig:
    """Tests for Config model."""

    def test_config_defaults(self):
        """Config should have sensible defaults."""
        config = Config()

        assert config.version == "1.0"
        assert config.project.name == "My Project"
        assert config.embeddings.model == "all-MiniLM-L6-v2"
        assert config.memory.max_facts == 1000
        assert not config.git.auto_commit

    def test_config_custom_values(self):
        """Config should accept custom values."""
        config = Config(
            project=ProjectConfig(name="Test Project", description="A test"),
        )

        assert config.project.name == "Test Project"
        assert config.project.description == "A test"


class TestBrainInfo:
    """Tests for BrainInfo model."""

    def test_total_memories(self):
        """Total memories should sum all types."""
        info = BrainInfo(
            project_name="Test",
            facts_count=10,
            decisions_count=5,
            learnings_count=3,
            preferences_count=2,
        )

        assert info.total_memories == 20
