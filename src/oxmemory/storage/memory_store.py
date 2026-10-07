"""Memory store abstraction for 0xMemory.

Provides a unified interface for storing and retrieving memories,
with dual storage: Markdown files (source of truth) + Vector DB (search).
"""

import logging
from datetime import datetime
from pathlib import Path

from oxmemory.core.config import brain_exists, get_brain_path, load_config
from oxmemory.core.models import BrainInfo, Memory, MemoryType, MemoryStatus
from oxmemory.storage.lifecycle import LifecycleMixin
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.session import SessionManager

logger = logging.getLogger(__name__)


class MemoryStore(LifecycleMixin):
    """Unified memory storage interface.

    Provides CRUD operations for memories with dual storage:
    - Markdown files: Source of truth, human-editable, Git-versioned
    - Vector DB: Semantic search via embeddings
    """

    def __init__(
        self,
        project_dir: Path | None = None,
        enable_vectors: bool = True,
    ):
        """Initialize the memory store.

        Args:
            project_dir: Project directory. Defaults to current directory.
            enable_vectors: Whether to enable vector search (requires chromadb).
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.markdown = MarkdownManager(self.project_dir)
        self.sessions = SessionManager(self.project_dir)
        self._config = None
        self._vector_store = None
        self._enable_vectors = enable_vectors

    @property
    def config(self):
        """Lazy-load configuration."""
        if self._config is None:
            try:
                self._config = load_config(self.project_dir)
            except FileNotFoundError:
                self._config = None
        return self._config

    def close(self) -> None:
        """Release initialized resources without loading optional backends."""
        if self._vector_store is not None:
            self._vector_store.close()
            self._vector_store = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def vector_store(self):
        """Lazy-load vector store."""
        if self._vector_store is None and self._enable_vectors:
            try:
                from oxmemory.storage.vector_store import VectorStore

                self._vector_store = VectorStore(self.project_dir)
            except ImportError:
                logger.warning("ChromaDB not installed, vector search disabled")
                self._enable_vectors = False
        return self._vector_store

    def is_initialized(self) -> bool:
        """Check if the brain is initialized.

        Returns:
            True if .0xmemory directory exists.
        """
        return brain_exists(self.project_dir)

    # -------------------------------------------------------------------------
    # Memory CRUD operations
    # -------------------------------------------------------------------------

    def add(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        tags: list[str] | None = None,
        source: str = "manual",
        salience: float = 0.5,
        file_paths: list[str] | None = None,
        symbols: list[str] | None = None,
        commit_sha: str | None = None,
        confidence: float | None = None,
    ) -> Memory:
        """Add a new memory.

        Args:
            content: Memory content.
            memory_type: Type of memory.
            tags: Optional categorization tags.
            source: Where this memory came from.
            salience: Importance score (0-1).

        Returns:
            Created Memory object.
        """
        memory = Memory(
            content=content,
            type=memory_type,
            tags=tags or [],
            source=source,
            salience=salience,
            file_paths=file_paths or [],
            symbols=symbols or [],
            commit_sha=commit_sha,
            confidence=confidence,
        )

        if commit_sha:
            from oxmemory.storage.repository import Repository
            memory.commit_sha = Repository(self.project_dir).validate_evidence(commit_sha, memory.file_paths)
        for existing in self.markdown.read_memories(memory_type):
            if (existing.status == MemoryStatus.ACTIVE
                and " ".join(existing.content.split()) == " ".join(memory.content.split())
                and existing.file_paths == memory.file_paths
                and existing.symbols == memory.symbols
                and existing.commit_sha == memory.commit_sha
                and existing.tags == memory.tags):
                return existing

        # Store in Markdown (source of truth)
        self.markdown.add_memory(memory)

        # Also add to vector store for semantic search
        if self.vector_store:
            try:
                self.vector_store.add(memory)
            except Exception as e:
                logger.warning(f"Failed to add to vector store: {e}")

        return memory

    def get(self, memory_id: str) -> Memory | None:
        """Get a memory by ID.

        Args:
            memory_id: Memory ID.

        Returns:
            Memory if found, None otherwise.
        """
        return self.markdown.get_memory_by_id(memory_id)

    def list_memories(
        self,
        memory_type: MemoryType | None = None,
        limit: int = 100,
        since: datetime | None = None,
    ) -> list[Memory]:
        """List memories with optional filters.

        Args:
            memory_type: Filter by type. None for all types.
            limit: Maximum number of results.
            since: Only return memories created after this time.

        Returns:
            List of matching memories.
        """
        if memory_type:
            memories = self.markdown.read_memories(memory_type)
        else:
            memories = self.markdown.get_all_memories()

        # Filter by date
        if since:
            memories = [m for m in memories if m.created_at >= since]

        # Sort by created_at descending (newest first)
        memories.sort(key=lambda m: m.created_at, reverse=True)

        return memories[:limit]

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: Memory ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        # Find the memory first to get its type
        memory = self.get(memory_id)
        if not memory:
            return False

        # Remove from Markdown
        removed = self.markdown.remove_memory(memory_id, memory.type)

        # Also remove from vector store
        if self.vector_store:
            try:
                self.vector_store.delete(memory_id)
            except Exception as e:
                logger.warning(f"Failed to remove from vector store: {e}")

        return removed

    def search(
        self, query: str, limit: int = 5,
        memory_types: list[MemoryType] | None = None, semantic: bool = True,
        file_paths: list[str] | None = None, symbols: list[str] | None = None,
        include_history: bool = False,
    ) -> list[Memory]:
        return [item["memory"] for item in self.search_ranked(
            query, limit, memory_types, semantic, file_paths, symbols, include_history,
        )]

    def search_ranked(
        self, query: str, limit: int = 5,
        memory_types: list[MemoryType] | None = None, semantic: bool = True,
        file_paths: list[str] | None = None, symbols: list[str] | None = None,
        include_history: bool = False, relevance_gate: bool | None = None,
        min_similarity: float | None = None,
    ) -> list[dict]:
        from oxmemory.storage.retrieval import rank_memories
        if relevance_gate is None:
            relevance_gate = self.config.retrieval.relevance_gate if self.config else False
        if min_similarity is None and self.config:
            min_similarity = self.config.retrieval.min_similarity
        return rank_memories(self, query, limit, memory_types, semantic,
                             file_paths, symbols, include_history,
                             relevance_gate=relevance_gate, min_similarity=min_similarity)

    def recall_context(self, query: str, token_budget: int = 1500, **kwargs) -> dict:
        from oxmemory.storage.retrieval import build_context
        return build_context(self.search_ranked(query, **kwargs), token_budget)

    def _keyword_search(
        self,
        query: str,
        limit: int = 5,
        memory_types: list[MemoryType] | None = None,
    ) -> list[Memory]:
        """Keyword-based search (fallback)."""
        # Get all memories to search
        if memory_types:
            memories = []
            for mt in memory_types:
                memories.extend(self.markdown.read_memories(mt))
        else:
            memories = self.markdown.get_all_memories()

        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_memories = []
        for memory in memories:
            content_lower = memory.content.lower()
            score = 0.0

            # Exact phrase match
            if query_lower in content_lower:
                score += 1.0

            # Word matches
            content_words = set(content_lower.split())
            matching_words = query_words & content_words
            if matching_words:
                score += len(matching_words) / len(query_words) * 0.5

            # Tag matches
            for tag in memory.tags:
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 0.3

            if score > 0:
                scored_memories.append((memory, score))

        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored_memories[:limit]]

    def update(self, memory_id: str, content: str) -> Memory | None:
        """Update a memory's content.

        Args:
            memory_id: Memory ID to update.
            content: New content.

        Returns:
            Updated Memory if found, None otherwise.
        """
        memory = self.get(memory_id)
        if not memory:
            return None

        content = Memory(content=content).content
        memory.revisions.append(memory.model_dump(mode="json", exclude={"revisions"}))
        memory.update_content(content)
        # Editing text does not validate changed code or reactivate stale evidence.
        self._persist(memory)

        return memory

    # -------------------------------------------------------------------------
    # Brain info
    # -------------------------------------------------------------------------

    def get_brain_info(self) -> BrainInfo:
        """Get brain statistics.

        Returns:
            BrainInfo with current stats.
        """
        counts = self.markdown.count_memories()

        # Get last modified time
        brain_path = get_brain_path(self.project_dir)
        last_updated = None
        if brain_path.exists():
            # Find most recently modified file
            for f in brain_path.rglob("*.md"):
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if last_updated is None or mtime > last_updated:
                    last_updated = mtime

        # Get project name from config if available
        project_name = "0xMemory"
        if self.config:
            project_name = self.config.project.name

        # Get session count
        sessions_count = len(self.sessions.list_sessions())

        return BrainInfo(
            project_name=project_name,
            facts_count=counts[MemoryType.FACT],
            decisions_count=counts[MemoryType.DECISION],
            learnings_count=counts[MemoryType.LEARNING],
            preferences_count=counts[MemoryType.PREFERENCE],
            sessions_count=sessions_count,
            last_updated=last_updated,
            brain_path=str(brain_path),
        )

    def get_brain_context(self) -> str:
        """Get the main brain context (brain.md content).

        Returns:
            Brain.md content.
        """
        return self.markdown.read_brain()

    def get_facts_context(self) -> str:
        """Get all facts as a formatted string for context.

        Returns:
            Formatted facts for LLM context.
        """
        memories = [m for m in self.markdown.read_memories(MemoryType.FACT) if m.status == MemoryStatus.ACTIVE]
        if not memories:
            return "No facts recorded yet."

        lines = ["## Known Facts\n"]
        for m in memories[:20]:  # Limit for context window
            tags = ", ".join(m.tags) if m.tags else "general"
            lines.append(f"- [{tags}] {m.content}")

        return "\n".join(lines)

    def get_decisions_context(self) -> str:
        """Get all decisions as a formatted string for context.

        Returns:
            Formatted decisions for LLM context.
        """
        memories = [m for m in self.markdown.read_memories(MemoryType.DECISION) if m.status == MemoryStatus.ACTIVE]
        if not memories:
            return "No decisions recorded yet."

        lines = ["## Past Decisions\n"]
        for m in memories[:10]:  # Limit for context window
            date = m.created_at.strftime("%Y-%m-%d")
            lines.append(f"- [{date}] {m.content}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Vector store maintenance
    # -------------------------------------------------------------------------

    def sync_vectors(self) -> dict:
        """Ensure vector store is in sync with Markdown files.

        Adds any memories missing from vector store.

        Returns:
            Dict with sync statistics.
        """
        if not self.vector_store:
            return {"synced": 0, "error": "Vector store not available"}

        memories = self.markdown.get_all_memories()
        vector_ids = set(self.vector_store.get_all_ids())
        current_ids = {m.id for m in memories}
        for memory in memories:
            self.vector_store.upsert(memory)
        for orphan in vector_ids - current_ids:
            self.vector_store.delete(orphan)
        return {"total_markdown": len(memories), "total_vectors": len(current_ids),
                "synced": len(memories), "removed": len(vector_ids - current_ids)}

    def rebuild_vectors(self) -> dict:
        """Rebuild vector store from Markdown files.

        Clears vector store and reindexes all memories from Markdown.
        Use this if vector store becomes corrupted or out of sync.

        Returns:
            Dict with rebuild statistics.
        """
        if not self.vector_store:
            return {"rebuilt": 0, "error": "Vector store not available"}

        all_memories = self.markdown.get_all_memories()
        count = self.vector_store.rebuild_from_memories(all_memories)

        return {
            "rebuilt": count,
            "facts": len([m for m in all_memories if m.type == MemoryType.FACT]),
            "decisions": len([m for m in all_memories if m.type == MemoryType.DECISION]),
            "learnings": len([m for m in all_memories if m.type == MemoryType.LEARNING]),
            "preferences": len([m for m in all_memories if m.type == MemoryType.PREFERENCE]),
        }
