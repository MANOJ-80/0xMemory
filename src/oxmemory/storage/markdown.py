"""Markdown file manager for 0xMemory.

Handles reading, writing, and parsing of human-editable Markdown files
that store brain context, facts, decisions, and other memories.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from oxmemory.core.models import Memory, MemoryType
from oxmemory.core.config import get_brain_path


# File names
BRAIN_FILE = "brain.md"
FACTS_FILE = "memory/facts.md"
DECISIONS_FILE = "memory/decisions.md"
LEARNINGS_FILE = "memory/learnings.md"
PREFERENCES_FILE = "memory/preferences.md"

# Memory entry pattern for parsing
# Matches: ## [YYYY-MM-DD HH:MM] `tag1` `tag2`
ENTRY_HEADER_PATTERN = re.compile(
    r'^##\s+\[(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)\]\s*((?:`[^`]+`\s*)*)\s*$'
)
# Matches: _ID: mem-xxxxxxxx_
ID_PATTERN = re.compile(r'_ID:\s*(\S+)_')
# Matches: _Source: xxxx_
SOURCE_PATTERN = re.compile(r'_Source:\s*(.+)_')


# Default brain.md template
BRAIN_TEMPLATE = '''# 🧠 Project Brain

> This is the main context file for your project.
> Edit this to help 0xMemory understand your project.

## Project Overview

{project_name} - {project_description}

## Architecture

[Describe key components and how they fit together]

## Conventions

[Document coding conventions, patterns, and rules]

## Current Focus

[What you're currently working on]

---

_Last updated: {date}_
'''

# Memory file templates
FACTS_TEMPLATE = '''# 📚 Facts & Knowledge

> Auto-extracted and manually added facts about the project.
> Feel free to edit, add, or remove entries!

---

'''

DECISIONS_TEMPLATE = '''# 🎯 Decisions & Rationale

> Important decisions with their context and reasoning.
> Helps understand why things are the way they are.

---

'''

LEARNINGS_TEMPLATE = '''# 💡 Learnings & Insights

> Lessons learned, gotchas, and insights from development.
> Prevents repeating the same mistakes.

---

'''

PREFERENCES_TEMPLATE = '''# ⚙️ Preferences

> User and project preferences for AI assistance.

---

'''


def serialize_memory_entry(memory: Memory) -> str:
    """Convert a Memory object to Markdown format.
    
    Args:
        memory: Memory object to serialize.
        
    Returns:
        Markdown string representation.
    """
    # Format timestamp
    timestamp = memory.created_at.strftime("%Y-%m-%d %H:%M")
    
    # Format tags
    tags_str = " ".join(f"`{tag}`" for tag in memory.tags) if memory.tags else ""
    
    # Build header
    header = f"## [{timestamp}]"
    if tags_str:
        header += f" {tags_str}"
    
    # Build content block
    lines = [
        header,
        "",
        memory.content,
        "",
        f"_Source: {memory.source}_",
        f"_ID: {memory.id}_",
        "",
        "---",
        "",
    ]
    
    return "\n".join(lines)


def parse_memory_entries(content: str, memory_type: MemoryType) -> list[Memory]:
    """Parse Memory entries from Markdown content.
    
    Args:
        content: Markdown file content.
        memory_type: Type to assign to parsed memories.
        
    Returns:
        List of Memory objects.
    """
    memories: list[Memory] = []
    
    # Split by entry headers
    lines = content.split("\n")
    current_entry: dict = {}
    current_content: list[str] = []
    
    for line in lines:
        header_match = ENTRY_HEADER_PATTERN.match(line)
        
        if header_match:
            # Save previous entry if exists
            if current_entry:
                current_entry["content"] = "\n".join(current_content).strip()
                memories.append(_build_memory(current_entry, memory_type))
            
            # Start new entry
            date_str = header_match.group(1)
            tags_str = header_match.group(2)
            
            # Parse date
            try:
                if " " in date_str:
                    created_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                else:
                    created_at = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                created_at = datetime.now()
            
            # Parse tags
            tags = re.findall(r'`([^`]+)`', tags_str)
            
            current_entry = {
                "created_at": created_at,
                "tags": tags,
                "id": None,
                "source": "manual",
            }
            current_content = []
            
        elif current_entry:
            # Check for metadata lines
            id_match = ID_PATTERN.search(line)
            source_match = SOURCE_PATTERN.search(line)
            
            if id_match:
                current_entry["id"] = id_match.group(1)
            elif source_match:
                current_entry["source"] = source_match.group(1)
            elif line.strip() != "---" and not line.startswith("_"):
                current_content.append(line)
    
    # Don't forget last entry
    if current_entry and current_content:
        current_entry["content"] = "\n".join(current_content).strip()
        memories.append(_build_memory(current_entry, memory_type))
    
    return memories


def _build_memory(entry: dict, memory_type: MemoryType) -> Memory:
    """Build a Memory object from parsed entry data."""
    return Memory(
        id=entry.get("id") or f"mem-{entry['created_at'].strftime('%Y%m%d%H%M%S')}",
        content=entry.get("content", ""),
        type=memory_type,
        tags=entry.get("tags", []),
        source=entry.get("source", "manual"),
        created_at=entry.get("created_at", datetime.now()),
        updated_at=entry.get("created_at", datetime.now()),
        accessed_at=datetime.now(),
    )


class MarkdownManager:
    """Manages Markdown files in the brain directory.
    
    Handles CRUD operations for brain.md, facts.md, decisions.md,
    and other memory files.
    """
    
    def __init__(self, project_dir: Optional[Path] = None):
        """Initialize the Markdown manager.
        
        Args:
            project_dir: Project directory. Defaults to current directory.
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.brain_path = get_brain_path(self.project_dir)
    
    # -------------------------------------------------------------------------
    # Brain.md operations
    # -------------------------------------------------------------------------
    
    def get_brain_file_path(self) -> Path:
        """Get path to brain.md."""
        return self.brain_path / BRAIN_FILE
    
    def read_brain(self) -> str:
        """Read brain.md content.
        
        Returns:
            Brain.md content, or empty string if not found.
        """
        brain_file = self.get_brain_file_path()
        if brain_file.exists():
            return brain_file.read_text()
        return ""
    
    def write_brain(self, content: str) -> None:
        """Write brain.md content.
        
        Args:
            content: Content to write.
        """
        brain_file = self.get_brain_file_path()
        brain_file.parent.mkdir(parents=True, exist_ok=True)
        brain_file.write_text(content)
    
    def create_brain(
        self, 
        project_name: str = "My Project",
        project_description: str = ""
    ) -> Path:
        """Create brain.md with template.
        
        Args:
            project_name: Project name to include.
            project_description: Optional project description.
            
        Returns:
            Path to created brain.md.
        """
        content = BRAIN_TEMPLATE.format(
            project_name=project_name,
            project_description=project_description or "Add your project description here",
            date=datetime.now().strftime("%Y-%m-%d"),
        )
        brain_file = self.get_brain_file_path()
        brain_file.parent.mkdir(parents=True, exist_ok=True)
        brain_file.write_text(content)
        return brain_file
    
    # -------------------------------------------------------------------------
    # Memory file operations
    # -------------------------------------------------------------------------
    
    def _get_memory_file_path(self, memory_type: MemoryType) -> Path:
        """Get file path for a memory type."""
        file_map = {
            MemoryType.FACT: FACTS_FILE,
            MemoryType.DECISION: DECISIONS_FILE,
            MemoryType.LEARNING: LEARNINGS_FILE,
            MemoryType.PREFERENCE: PREFERENCES_FILE,
        }
        return self.brain_path / file_map[memory_type]
    
    def _get_template(self, memory_type: MemoryType) -> str:
        """Get template for a memory type."""
        template_map = {
            MemoryType.FACT: FACTS_TEMPLATE,
            MemoryType.DECISION: DECISIONS_TEMPLATE,
            MemoryType.LEARNING: LEARNINGS_TEMPLATE,
            MemoryType.PREFERENCE: PREFERENCES_TEMPLATE,
        }
        return template_map[memory_type]
    
    def create_memory_files(self) -> list[Path]:
        """Create all memory files with templates.
        
        Returns:
            List of created file paths.
        """
        created = []
        for memory_type in MemoryType:
            file_path = self._get_memory_file_path(memory_type)
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(self._get_template(memory_type))
                created.append(file_path)
        return created
    
    def read_memories(self, memory_type: MemoryType) -> list[Memory]:
        """Read all memories of a given type.
        
        Args:
            memory_type: Type of memories to read.
            
        Returns:
            List of Memory objects.
        """
        file_path = self._get_memory_file_path(memory_type)
        if not file_path.exists():
            return []
        
        content = file_path.read_text()
        return parse_memory_entries(content, memory_type)
    
    def add_memory(self, memory: Memory) -> None:
        """Add a memory to the appropriate file.
        
        Args:
            memory: Memory to add.
        """
        file_path = self._get_memory_file_path(memory.type)
        
        # Ensure file exists with template
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(self._get_template(memory.type))
        
        # Append new memory
        entry = serialize_memory_entry(memory)
        with open(file_path, 'a') as f:
            f.write(entry)
    
    def remove_memory(self, memory_id: str, memory_type: MemoryType) -> bool:
        """Remove a memory by ID.
        
        Args:
            memory_id: ID of memory to remove.
            memory_type: Type of memory.
            
        Returns:
            True if removed, False if not found.
        """
        file_path = self._get_memory_file_path(memory_type)
        if not file_path.exists():
            return False
        
        content = file_path.read_text()
        
        # Find and remove the entry
        # Pattern matches from header to next separator
        pattern = rf'(## \[[^\]]+\].*?_ID:\s*{re.escape(memory_id)}_.*?---\n*)'
        
        new_content, count = re.subn(pattern, '', content, flags=re.DOTALL)
        
        if count > 0:
            file_path.write_text(new_content)
            return True
        return False
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """Find a memory by ID across all types.
        
        Args:
            memory_id: ID to search for.
            
        Returns:
            Memory if found, None otherwise.
        """
        for memory_type in MemoryType:
            memories = self.read_memories(memory_type)
            for memory in memories:
                if memory.id == memory_id:
                    return memory
        return None
    
    def get_all_memories(self) -> list[Memory]:
        """Get all memories of all types.
        
        Returns:
            List of all Memory objects.
        """
        all_memories = []
        for memory_type in MemoryType:
            all_memories.extend(self.read_memories(memory_type))
        return all_memories
    
    def count_memories(self) -> dict[MemoryType, int]:
        """Count memories by type.
        
        Returns:
            Dictionary mapping memory type to count.
        """
        return {
            memory_type: len(self.read_memories(memory_type))
            for memory_type in MemoryType
        }
    
    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------
    
    def initialize_brain(
        self,
        project_name: str = "My Project",
        project_description: str = "",
    ) -> dict[str, Path]:
        """Initialize all brain files.
        
        Args:
            project_name: Project name.
            project_description: Project description.
            
        Returns:
            Dictionary of created files.
        """
        created = {}
        
        # Create brain.md
        brain_file = self.create_brain(project_name, project_description)
        created["brain"] = brain_file
        
        # Create memory files
        memory_files = self.create_memory_files()
        for f in memory_files:
            created[f.stem] = f
        
        # Create directories
        docs_dir = self.brain_path / "documents"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        sessions_dir = self.brain_path / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        store_dir = self.brain_path / ".store"
        store_dir.mkdir(parents=True, exist_ok=True)
        
        return created
