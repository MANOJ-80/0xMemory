"""MCP resource providers for 0xMemory.

Defines resources that AI clients can read to get context.
"""

from oxmemory.storage.memory_store import MemoryStore


async def get_brain_context(store: MemoryStore) -> str:
    """Get the main project brain context (brain.md).
    
    Args:
        store: Memory store instance.
        
    Returns:
        Brain.md content.
    """
    return store.get_brain_context()


async def get_facts_context(store: MemoryStore) -> str:
    """Get known facts formatted for context.
    
    Args:
        store: Memory store instance.
        
    Returns:
        Formatted facts.
    """
    return store.get_facts_context()


async def get_decisions_context(store: MemoryStore) -> str:
    """Get past decisions formatted for context.
    
    Args:
        store: Memory store instance.
        
    Returns:
        Formatted decisions.
    """
    return store.get_decisions_context()


async def get_full_context(store: MemoryStore) -> str:
    """Get full project context combining brain, facts, and decisions.
    
    Args:
        store: Memory store instance.
        
    Returns:
        Combined context string.
    """
    brain = store.get_brain_context()
    facts = store.get_facts_context()
    decisions = store.get_decisions_context()
    
    sections = []
    
    if brain:
        sections.append(brain)
    
    sections.append("\n---\n")
    sections.append(facts)
    sections.append("\n---\n")
    sections.append(decisions)
    
    return "\n".join(sections)
