"""Core data models for 0xMemory."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import PurePosixPath
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class MemoryType(str, Enum):
    """Types of memories that can be stored."""

    FACT = "fact"
    DECISION = "decision"
    LEARNING = "learning"
    PREFERENCE = "preference"
    TASK_STATE = "task_state"
    ENVIRONMENT = "environment"


class MemoryStatus(str, Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    ACTIVE_UNVERIFIED = "active_unverified"
    ACTIVE_VERIFIED = "active_verified"
    STALE = "stale"
    REVIEW_REQUIRED = "review_required"
    LIKELY_FALSE = "likely_false"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    QUARANTINED = "quarantined"


class Memory(BaseModel):
    """A single memory entry.

    Represents a piece of knowledge stored in the brain, such as
    a fact, decision, learning, or user preference.
    """

    id: str = Field(default_factory=lambda: f"mem-{uuid4().hex[:8]}")
    schema_version: int = 3
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
    status: MemoryStatus = MemoryStatus.ACTIVE
    file_paths: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    commit_sha: str | None = None
    evidence_branch: str | None = Field(
        default=None, description="Branch on which linked evidence was reviewed"
    )
    confidence: float | None = Field(
        default=None, ge=0, le=1,
        description="Capture/extraction confidence; distinct from repository evidence support.",
    )
    claim_confidence: float | None = Field(
        default=None, ge=0, le=1,
        description="Estimated confidence that the claim is true; separate from extraction confidence.",
    )
    supersedes: str | None = None
    superseded_by: str | None = None
    verification_note: str | None = None
    stale_at_commit: str | None = None
    revisions: list[dict] = Field(default_factory=list)
    scope_type: str = Field(default="project", description="project, branch, task, or user")
    scope_id: str | None = None
    provenance: dict = Field(default_factory=dict)
    trust_basis: str = Field(default="user_asserted")
    answer_slots: dict[str, str] = Field(default_factory=dict)
    sensitivity: str = Field(default="normal")
    # Claim validity is separate from record expiry/review scheduling.
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    claim_subject: str | None = None
    claim_predicate: str | None = None
    claim_value: str | None = None
    claim_environment: str | None = None
    # Distinguishes a proposed/evaluated option from an adopted project decision.
    # This is orthogonal to lifecycle status (active, review-required, superseded).
    claim_state: str = Field(default="asserted", description="asserted, proposed, evaluating, adopted, rejected, unknown")
    valid_until: datetime | None = None
    review_after: datetime | None = None
    utility: float = Field(default=0.0, ge=0.0, le=1.0)
    utility_observations: int = Field(default=0, ge=0)
    evidence_refs: list[dict] = Field(default_factory=list)

    @field_validator("content")
    @classmethod
    def nonempty_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Memory content cannot be empty")
        return value.strip()

    @field_validator("file_paths")
    @classmethod
    def normalize_paths(cls, values: list[str]) -> list[str]:
        paths = []
        for value in values:
            value = value.replace("\\", "/")
            path = PurePosixPath(value)
            if not value or path.is_absolute() or ".." in path.parts or ":" in value:
                raise ValueError("Evidence paths must be repository-relative")
            if str(path) == ".":
                raise ValueError("Evidence must reference a file")
            paths.append(str(path))
        return list(dict.fromkeys(paths))

    @model_validator(mode="after")
    def validate_scope_and_sensitivity(self):
        if self.scope_type not in {"project", "branch", "task", "user"}:
            raise ValueError("scope_type must be project, branch, task, or user")
        if self.scope_type in {"branch", "task", "user"} and not self.scope_id:
            raise ValueError(f"scope_id is required for {self.scope_type}-scoped memories")
        if self.sensitivity not in {"normal", "sensitive", "secret"}:
            raise ValueError("sensitivity must be normal, sensitive, or secret")
        if self.claim_state not in {"asserted", "proposed", "evaluating", "adopted", "rejected", "unknown"}:
            raise ValueError("claim_state must be asserted, proposed, evaluating, adopted, rejected, or unknown")
        if self.valid_from and self.valid_to:
            valid_from = (self.valid_from.replace(tzinfo=timezone.utc) if self.valid_from.tzinfo is None
                          else self.valid_from.astimezone(timezone.utc))
            valid_to = (self.valid_to.replace(tzinfo=timezone.utc) if self.valid_to.tzinfo is None
                        else self.valid_to.astimezone(timezone.utc))
            if valid_to <= valid_from:
                raise ValueError("valid_to must be later than valid_from (validity uses [from, to))")
        structured_claim = (self.claim_subject, self.claim_predicate, self.claim_value)
        if any((*structured_claim, self.claim_environment)) and not all(structured_claim):
            raise ValueError("Structured claims require claim_subject, claim_predicate, and claim_value")
        if self.type == MemoryType.TASK_STATE:
            if self.scope_type != "task" or not self.scope_id:
                raise ValueError("task_state memories require task scope and a task scope_id")
            if self.valid_until is None:
                self.valid_until = datetime.now() + timedelta(days=7)
        return self

    def touch(self) -> None:
        """Mark memory as accessed (updates accessed_at)."""
        self.accessed_at = datetime.now()

    def update_content(self, content: str) -> None:
        """Update memory content and timestamp."""
        self.content = content
        self.updated_at = datetime.now()

    @property
    def is_recallable(self) -> bool:
        """Whether lifecycle policy permits ordinary recall of this record."""
        return self.status in {
            MemoryStatus.ACTIVE, MemoryStatus.ACTIVE_UNVERIFIED,
            MemoryStatus.ACTIVE_VERIFIED, MemoryStatus.REVIEW_REQUIRED,
        }

    @property
    def is_expired(self) -> bool:
        if self.valid_until is None:
            return False
        now = datetime.now(self.valid_until.tzinfo) if self.valid_until.tzinfo else datetime.now()
        return self.valid_until <= now


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


class RetrievalConfig(BaseModel):
    """EDAM retrieval policy. Weights are configurable for development-data tuning."""

    architecture: str = "edam"
    relevance_gate: bool = True
    min_similarity: float = Field(default=0.25, ge=-1, le=1, allow_inf_nan=False)
    # Keep the EDAM floor low enough to retain paraphrased evidence; the
    # relevance gate and downstream conflict/validity checks still control
    # unsafe memories. A high floor caused valid low-salience facts to vanish.
    min_edam_score: float = Field(default=0.12, ge=0, le=1, allow_inf_nan=False)
    w_relevance: float = Field(default=0.45, ge=0, le=1, allow_inf_nan=False)
    w_evidence: float = Field(default=0.15, ge=0, le=1, allow_inf_nan=False)
    w_temporal: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    w_freshness: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    w_scope: float = Field(default=0.10, ge=0, le=1, allow_inf_nan=False)
    w_utility: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    w_provenance: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    w_confidence: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    w_extraction_confidence: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    redundancy_threshold: float = Field(default=0.82, ge=0, le=1, allow_inf_nan=False)
    freshness_half_life_days: int = Field(default=365, ge=1, le=36500)
    abstain_on_conflict: bool = True
    baseline_mode: bool = False

    @model_validator(mode="after")
    def validate_edam_weights(self):
        weights = (self.w_relevance, self.w_evidence, self.w_temporal, self.w_freshness,
                   self.w_scope, self.w_utility, self.w_provenance, self.w_confidence,
                   self.w_extraction_confidence)
        if sum(weights) <= 0:
            raise ValueError("At least one EDAM ranking weight must be positive")
        if self.architecture not in {"edam", "baseline"}:
            raise ValueError("retrieval.architecture must be 'edam' or 'baseline'")
        return self


class Config(BaseModel):
    """Main configuration schema for 0xMemory."""

    version: str = Field(default="1.0", description="Config schema version")
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
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
    task_states_count: int = 0
    environment_count: int = 0
    sessions_count: int = 0
    last_updated: datetime | None = None
    brain_path: str = ""

    @property
    def total_memories(self) -> int:
        """Total number of memories stored."""
        return (
            self.facts_count + self.decisions_count + self.learnings_count + self.preferences_count
            + self.task_states_count + self.environment_count
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
