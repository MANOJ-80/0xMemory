"""MCP tool implementations for 0xMemory.

Defines the tools that AI clients can use to interact with the memory store.
"""

from oxmemory.core.models import Memory, MemoryType
from oxmemory.storage.memory_store import MemoryStore


def _memory_to_dict(memory: Memory) -> dict:
    """Convert a Memory to a serializable dictionary."""
    return memory.model_dump(mode="json")


async def handle_remember(
    store: MemoryStore,
    content: str,
    type: str = "fact",
    tags: list[str] | None = None,
    source: str = "conversation",
    file_paths: list[str] | None = None,
    symbols: list[str] | None = None,
    commit_sha: str | None = None,
    scope_type: str = "project",
    scope_id: str | None = None,
    answer_slots: dict[str, str] | None = None,
    sensitivity: str = "normal",
    propose: bool = False,
    valid_until: str | None = None,
    review_after: str | None = None,
) -> dict:
    """Handle the 'remember' tool call.

    Store a new memory (fact, decision, learning, or preference).

    Args:
        store: Memory store instance.
        content: The memory content to store.
        type: Type of memory (fact, decision, learning, preference).
        tags: Optional categorization tags.
        source: Where this memory came from.

    Returns:
        Dictionary with success status and memory ID.
    """
    try:
        # Parse memory type
        memory_type = MemoryType(type.lower())
    except ValueError:
        return {
            "success": False,
            "error": f"Invalid memory type: {type}. Must be one of: "
            "fact, decision, learning, preference, task_state, environment",
        }

    try:
        save = store.propose if propose else store.add
        memory = save(
            content=content,
            memory_type=memory_type,
            tags=tags or [],
            source=source,
            file_paths=file_paths,
            symbols=symbols,
            commit_sha=commit_sha,
            scope_type=scope_type,
            scope_id=scope_id,
            answer_slots=answer_slots,
            sensitivity=sensitivity,
            provenance={"source": source, "capture": "candidate" if propose else "direct"},
            valid_until=valid_until,
            review_after=review_after,
        )

        action = ("Proposed" if memory.status.value == "candidate" else "Reused existing") if propose else "Stored"
        return {
            "success": True,
            "id": memory.id,
            "status": memory.status.value,
            "message": f"{action} {memory_type.value}: "
            f"{content[:50]}{'...' if len(content) > 50 else ''}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_recall(
    store: MemoryStore,
    query: str,
    limit: int = 5,
    types: list[str] | None = None,
    file_paths: list[str] | None = None,
    symbols: list[str] | None = None,
    include_history: bool = False,
    token_budget: int = 1500,
    task_context: str | None = None,
    task_id: str | None = None,
    include_sensitive: bool = False,
    user_scope_id: str | None = None,
) -> dict:
    """Handle the 'recall' tool call.

    Search memories by meaning/content.

    Args:
        store: Memory store instance.
        query: Natural language search query.
        limit: Maximum number of results.
        types: Filter by memory types.

    Returns:
        Dictionary with matching memories.
    """
    try:
        # Parse memory types filter
        memory_types = None
        if types:
            memory_types = []
            for t in types:
                try:
                    memory_types.append(MemoryType(t.lower()))
                except ValueError:
                    pass  # Ignore invalid types

        context = store.recall_context(
            query=query,
            limit=limit,
            memory_types=memory_types,
            file_paths=file_paths, symbols=symbols,
            include_history=include_history, token_budget=token_budget,
            task_context=task_context,
            scope_context={key: value for key, value in {
                "task": task_id, "user": user_scope_id,
            }.items() if value},
            include_sensitive=include_sensitive,
        )
        memories = [item["memory"] for item in context["results"]]

        if not memories:
            return {
                "found": 0,
                "memories": [],
                "context": context,
                "message": ("No memories fit the context budget."
                            if context["abstention_reason"] == "context_budget"
                            else "No relevant memory found. Do not infer an answer from unrelated memories."),
            }

        return {
            "found": len(memories),
            "memories": memories,
            "context": context,
            "message": f"Found {len(memories)} relevant memories",
        }
    except Exception as e:
        return {
            "found": 0,
            "memories": [],
            "error": str(e),
        }


async def handle_list(
    store: MemoryStore,
    type: str | None = None,
    limit: int = 20,
    include_sensitive: bool = False,
) -> dict:
    """Handle the 'list' tool call.

    List all memories, optionally filtered by type.

    Args:
        store: Memory store instance.
        type: Filter by memory type.
        limit: Maximum number of results.

    Returns:
        Dictionary with memory list.
    """
    try:
        memory_type = None
        if type:
            try:
                memory_type = MemoryType(type.lower())
            except ValueError:
                return {
                    "count": 0,
                    "memories": [],
                    "error": f"Invalid memory type: {type}",
                }

        memories = store.list_memories(
            memory_type=memory_type,
            limit=min(max(limit, 1), 1000),
        )
        memories = [m for m in memories if m.sensitivity == "normal" or
                    (include_sensitive and m.sensitivity == "sensitive")]

        return {
            "count": len(memories),
            "memories": [_memory_to_dict(m) for m in memories],
        }
    except Exception as e:
        return {
            "count": 0,
            "memories": [],
            "error": str(e),
        }


async def handle_forget(
    store: MemoryStore,
    id: str,
) -> dict:
    """Handle the 'forget' tool call.

    Remove a memory by ID.

    Args:
        store: Memory store instance.
        id: Memory ID to remove.

    Returns:
        Dictionary with success status.
    """
    try:
        removed = store.delete(id)

        if removed:
            return {
                "success": True,
                "message": f"Removed memory: {id}",
            }
        else:
            return {
                "success": False,
                "error": f"Memory not found: {id}",
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_update(
    store: MemoryStore,
    id: str,
    content: str,
) -> dict:
    """Handle the 'update' tool call.

    Update an existing memory's content.

    Args:
        store: Memory store instance.
        id: Memory ID to update.
        content: New content.

    Returns:
        Dictionary with success status.
    """
    try:
        memory = store.update(id, content)

        if memory:
            return {
                "success": True,
                "id": memory.id,
                "message": f"Updated memory: {id}",
            }
        else:
            return {
                "success": False,
                "error": f"Memory not found: {id}",
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def handle_status(store: MemoryStore) -> dict:
    """Handle the 'status' tool call.

    Get brain statistics.

    Args:
        store: Memory store instance.

    Returns:
        Dictionary with brain info.
    """
    try:
        info = store.get_brain_info()

        return {
            "project_name": info.project_name,
            "total_memories": info.total_memories,
            "facts": info.facts_count,
            "decisions": info.decisions_count,
            "learnings": info.learnings_count,
            "preferences": info.preferences_count,
            "task_states": info.task_states_count,
            "environment": info.environment_count,
            "last_updated": info.last_updated.isoformat() if info.last_updated else None,
            "brain_path": info.brain_path,
            "event_ledger": store.events.status(),
        }
    except Exception as e:
        return {
            "error": str(e),
        }


async def handle_activity(store: MemoryStore, limit: int = 100) -> dict:
    try:
        return {"events": store.activity(limit), "ledger": store.events.status()}
    except Exception as e:
        return {"events": [], "error": str(e)}


async def handle_extract(
    store: MemoryStore,
    conversation: str,
    auto_save: bool = True,
) -> dict:
    """Handle the 'extract' tool call.

    Extract facts, decisions, and learnings from a conversation using LLM.

    Args:
        store: Memory store instance.
        conversation: The conversation to analyze.
        auto_save: Whether to automatically save extracted memories.

    Returns:
        Dictionary with extracted knowledge.
    """
    try:
        from oxmemory.extraction import KnowledgeExtractor

        extractor = KnowledgeExtractor()

        if not extractor.is_available():
            return {
                "success": False,
                "error": "No LLM provider available. Configure Ollama, Groq, or Gemini.",
            }

        result = await extractor.extract(conversation)

        if result.error:
            return {
                "success": False,
                "error": result.error,
            }

        saved_count = 0
        candidate_ids = []
        if auto_save:
            memories = extractor.extraction_to_memories(result)
            for memory in memories:
                candidate = store.propose(
                    content=memory.content,
                    memory_type=memory.type,
                    tags=memory.tags,
                    source="extraction",
                    salience=memory.salience,
                    confidence=memory.confidence,
                    provenance={"source": "conversation_extraction", "trust": "model_inferred"},
                )
                saved_count += 1
                candidate_ids.append(candidate.id)

        return {
            "success": True,
            "facts": result.facts,
            "decisions": result.decisions,
            "learnings": result.learnings,
            "saved_candidates": saved_count,
            "candidate_ids": candidate_ids,
            "review_required": bool(candidate_ids),
            "message": f"Extracted {len(result.facts)} facts, "
            f"{len(result.decisions)} decisions, {len(result.learnings)} learnings; "
            f"proposed {saved_count} candidate(s) for review",
        }

    except ImportError:
        return {
            "success": False,
            "error": "Extraction module not available. Install litellm.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
