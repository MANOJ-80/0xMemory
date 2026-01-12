"""Core data models for 0xMemory."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memories that can be stored."""

    FACT = "fact"
    DECISION = "decision"
    LEARNING = "learning"
    PREFERENCE = "preference"


class Memory(BaseModel):
    """A single memory entry.

    Represents a piece of knowledge stored in the brain, such as
    a fact, decision, learning, or user preference.
    """

    id: str = Field(default_factory=lambda: f"mem-{uuid4().hex[:8]}")
    content: str = Field(..., description="The memory content")
    type: MemoryType = Field(default=MemoryType.FACT, description="Type of memory")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    source: str = Field(default="manual", description="Where this memory came from")
    salience: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score (0-1)")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    accessed_at: datetime = Field(default_factory=datetime.now)

    # Optional metadata
    session_id: str | None = Field(default=None, description="Session that created this")
    related_to: list[str] = Field(default_factory=list, description="Related memory IDs")

    def touch(self) -> None:
        """Mark memory as accessed (updates accessed_at)."""
        self.accessed_at = datetime.now()

    def update_content(self, content: str) -> None:
        """Update memory content and timestamp."""
        self.content = content
        self.updated_at = datetime.now()


class ProjectConfig(BaseModel):
    """Project identification settings."""

    name: str = Field(default="My Project", description="Project name")
    description: str = Field(default="", description="Project description")


class EmbeddingsConfig(BaseModel):
    """Embedding model configuration."""

    model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model name")
    # For cloud embeddings (optional, Phase 2+)
    api_key_env: str | None = Field(default=None, description="Environment variable for API key")


class MemoryConfig(BaseModel):
    """Memory behavior settings."""

    max_facts: int = Field(default=1000, description="Maximum facts to store")
    decay_enabled: bool = Field(default=False, description="Enable memory decay")
    decay_rate: float = Field(default=0.01, description="Decay rate per day")
    consolidation_interval: str = Field(default="weekly", description="Consolidation schedule")


class GitConfig(BaseModel):
    """Git integration settings."""

    auto_commit: bool = Field(default=False, description="Auto-commit memory changes")
    commit_prefix: str = Field(default="[0xMemory]", description="Commit message prefix")


class LLMProviderConfig(BaseModel):
    """LLM provider configuration for knowledge extraction."""

    provider: str = Field(default="ollama", description="LLM provider name")
    model: str = Field(default="llama3.2:3b", description="Model name")
    api_key_env: str | None = Field(default=None, description="API key env var")
    host: str | None = Field(default=None, description="Custom host URL")


class LLMConfig(BaseModel):
    """LLM configuration for knowledge extraction (Phase 3)."""

    enabled: bool = Field(default=False, description="Enable LLM extraction")
    providers: list[LLMProviderConfig] = Field(
        default_factory=lambda: [LLMProviderConfig()], description="LLM providers in priority order"
    )


class Config(BaseModel):
    """Main configuration schema for 0xMemory."""

    version: str = Field(default="1.0", description="Config schema version")
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


class BrainInfo(BaseModel):
    """Statistics about the brain."""

    project_name: str
    facts_count: int = 0
    decisions_count: int = 0
    learnings_count: int = 0
    preferences_count: int = 0
    sessions_count: int = 0
    last_updated: datetime | None = None
    brain_path: str = ""

    @property
    def total_memories(self) -> int:
        """Total number of memories stored."""
        return (
            self.facts_count + self.decisions_count + self.learnings_count + self.preferences_count
        )


class Message(BaseModel):
    """A single message in a chat session."""

    role: str = Field(..., description="Role (user, assistant, system, tool)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_calls: list[dict] | None = None
    tool_results: list[dict] | None = None


class Session(BaseModel):
    """A chat session."""

    id: str = Field(default_factory=lambda: f"sess-{uuid4().hex[:8]}")
    title: str = Field(default="New Session")
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
