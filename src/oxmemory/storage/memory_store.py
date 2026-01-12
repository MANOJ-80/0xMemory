"""Memory store abstraction for 0xMemory.

Provides a unified interface for storing and retrieving memories,
with dual storage: Markdown files (source of truth) + Vector DB (search).
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from oxmemory.core.models import Memory, MemoryType, BrainInfo
from oxmemory.core.config import load_config, brain_exists, get_brain_path
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.session import SessionManager

logger = logging.getLogger(__name__)


class MemoryStore:
    """Unified memory storage interface.
    
    Provides CRUD operations for memories with dual storage:
    - Markdown files: Source of truth, human-editable, Git-versioned
    - Vector DB: Semantic search via embeddings
    """
    
    def __init__(
        self, 
        project_dir: Optional[Path] = None,
        enable_vectors: bool = True,
    ):
        """Initialize the memory store.
        
        Args:
            project_dir: Project directory. Defaults to current directory.
            enable_vectors: Whether to enable vector search (requires chromadb).
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
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
        tags: Optional[List[str]] = None,
        source: str = "manual",
        salience: float = 0.5,
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
        )
        
        # Store in Markdown (source of truth)
        self.markdown.add_memory(memory)
        
        # Also add to vector store for semantic search
        if self.vector_store:
            try:
                self.vector_store.add(memory)
            except Exception as e:
                logger.warning(f"Failed to add to vector store: {e}")
        
        return memory
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID.
        
        Args:
            memory_id: Memory ID.
            
        Returns:
            Memory if found, None otherwise.
        """
        return self.markdown.get_memory_by_id(memory_id)
    
    def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Memory]:
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
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
        semantic: bool = True,
    ) -> List[Memory]:
        """Search memories by content using hybrid search.
        
        Combines semantic (vector) search with keyword matching for best results.
        
        Args:
            query: Search query.
            limit: Maximum number of results.
            memory_types: Filter by types. None for all types.
            semantic: Use semantic search if available.
            
        Returns:
            List of matching memories, sorted by relevance.
        """
        # Try semantic search first if enabled
        if semantic and self.vector_store:
            try:
                vector_results = self.vector_store.search(
                    query=query,
                    limit=limit * 2,  # Get more for reranking
                    memory_types=memory_types,
                )
                
                if vector_results:
                    # Convert vector results to Memory objects
                    memories = []
                    for result in vector_results[:limit]:
                        memory = self.get(result["id"])
                        if memory:
                            memories.append(memory)
                    
                    if memories:
                        return memories
            except Exception as e:
                logger.warning(f"Vector search failed, falling back to keyword: {e}")
        
        # Fallback to keyword search
        return self._keyword_search(query, limit, memory_types)
    
    def _keyword_search(
        self,
        query: str,
        limit: int = 5,
        memory_types: Optional[List[MemoryType]] = None,
    ) -> List[Memory]:
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
    
    def update(self, memory_id: str, content: str) -> Optional[Memory]:
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
        
        # Remove old and add new (simple approach for Phase 1)
        self.delete(memory_id)
        
        memory.update_content(content)
        self.markdown.add_memory(memory)
        
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
        project_name = "Unknown Project"
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
            last_updated=datetime.now(),
            brain_path=str(self.project_dir)
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
        memories = self.markdown.read_memories(MemoryType.FACT)
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
        memories = self.markdown.read_memories(MemoryType.DECISION)
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
        
        markdown_memories = self.markdown.get_all_memories()
        vector_ids = set(self.vector_store.get_all_ids())
        
        missing = []
        for memory in markdown_memories:
            if memory.id not in vector_ids:
                missing.append(memory)
        
        if missing:
            self.vector_store.add_many(missing)
        
        return {
            "total_markdown": len(markdown_memories),
            "total_vectors": len(vector_ids),
            "synced": len(missing),
        }
    
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

