"""Integration tests for 0xMemory MCP server.

Tests end-to-end functionality by spawning the server and simulating tool calls.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from oxmemory.mcp.server import create_server
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.core.config import save_config, get_default_config


@pytest.fixture
def temp_project():
    """Create a temporary project directory with initialized brain."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        
        # Initialize brain
        config = get_default_config("Test Project")
        save_config(config, project_dir)
        
        markdown = MarkdownManager(project_dir)
        markdown.initialize_brain("Test Project", "A test project")
        
        yield project_dir


class TestMCPServerCreation:
    """Tests for MCP server creation."""
    
    def test_create_server_returns_tuple(self, temp_project):
        """Server creation returns (Server, MemoryStore) tuple."""
        server, store = create_server(temp_project)
        
        assert server is not None
        assert store is not None
        assert store.is_initialized()
    
    def test_server_has_name(self, temp_project):
        """Server has correct name."""
        server, _ = create_server(temp_project)
        
        # Server name should be set
        assert server.name == "0xmemory"


class TestMCPTools:
    """Tests for MCP tool handlers."""
    
    @pytest.fixture
    def server_and_store(self, temp_project):
        """Create server and store."""
        return create_server(temp_project)
    
    @pytest.mark.asyncio
    async def test_remember_tool(self, server_and_store):
        """Test the remember tool stores a memory."""
        server, store = server_and_store
        
        # Simulate calling the remember tool
        from oxmemory.mcp.tools import handle_remember
        
        result = await handle_remember(
            store=store,
            content="The API uses port 8080",
            type="fact",
            tags=["api", "config"],
            source="test",
        )
        
        assert result["success"] is True
        assert "id" in result
        assert result["id"].startswith("mem-")
        
        # Verify memory was saved
        memories = store.list_memories()
        assert len(memories) == 1
        assert memories[0].content == "The API uses port 8080"
        assert "api" in memories[0].tags
    
    @pytest.mark.asyncio
    async def test_recall_tool(self, server_and_store):
        """Test the recall tool retrieves memories."""
        server, store = server_and_store
        
        # Add some memories first
        from oxmemory.core.models import MemoryType
        store.add("We use PostgreSQL for the database", MemoryType.FACT, ["db"])
        store.add("Frontend uses React", MemoryType.FACT, ["frontend"])
        
        # Test recall
        from oxmemory.mcp.tools import handle_recall
        
        result = await handle_recall(
            store=store,
            query="database",
            limit=5,
            types=None,
        )
        
        assert "memories" in result
        # Should find the PostgreSQL memory
        contents = [m["content"] for m in result["memories"]]
        assert any("PostgreSQL" in c for c in contents)
    
    @pytest.mark.asyncio
    async def test_list_tool(self, server_and_store):
        """Test the list tool returns all memories."""
        server, store = server_and_store
        
        # Add memories
        from oxmemory.core.models import MemoryType
        store.add("Fact 1", MemoryType.FACT)
        store.add("Fact 2", MemoryType.FACT)
        store.add("Decision 1", MemoryType.DECISION)
        
        from oxmemory.mcp.tools import handle_list
        
        # List all
        result = await handle_list(store=store, type=None, limit=20)
        assert len(result["memories"]) == 3
        
        # List only facts
        result = await handle_list(store=store, type="fact", limit=20)
        assert len(result["memories"]) == 2
    
    @pytest.mark.asyncio
    async def test_forget_tool(self, server_and_store):
        """Test the forget tool removes a memory."""
        server, store = server_and_store
        
        # Add a memory
        from oxmemory.core.models import MemoryType
        memory = store.add("To be deleted", MemoryType.FACT)
        memory_id = memory.id
        
        # Delete it
        from oxmemory.mcp.tools import handle_forget
        
        result = await handle_forget(store=store, id=memory_id)
        assert result["success"] is True
        
        # Verify it's gone
        assert store.get(memory_id) is None
    
    @pytest.mark.asyncio
    async def test_update_tool(self, server_and_store):
        """Test the update tool modifies a memory."""
        server, store = server_and_store
        
        # Add a memory
        from oxmemory.core.models import MemoryType
        memory = store.add("Original content", MemoryType.FACT)
        memory_id = memory.id
        
        # Update it
        from oxmemory.mcp.tools import handle_update
        
        result = await handle_update(
            store=store,
            id=memory_id,
            content="Updated content",
        )
        assert result["success"] is True
        
        # Verify update
        updated = store.get(memory_id)
        assert updated.content == "Updated content"
    
    @pytest.mark.asyncio
    async def test_status_tool(self, server_and_store):
        """Test the status tool returns brain info."""
        server, store = server_and_store
        
        # Add some memories
        from oxmemory.core.models import MemoryType
        store.add("Fact", MemoryType.FACT)
        store.add("Decision", MemoryType.DECISION)
        
        from oxmemory.mcp.tools import handle_status
        
        result = await handle_status(store)
        
        assert "project_name" in result
        assert result["facts"] == 1
        assert result["decisions"] == 1


class TestMCPResources:
    """Tests for MCP resource handlers."""
    
    @pytest.fixture
    def store(self, temp_project):
        """Create a memory store."""
        _, store = create_server(temp_project)
        return store
    
    @pytest.mark.asyncio
    async def test_brain_context_resource(self, store):
        """Test reading brain://context resource."""
        from oxmemory.mcp.resources import get_brain_context
        
        content = await get_brain_context(store)
        
        assert "Test Project" in content
        assert "# 🧠 Project Brain" in content
    
    @pytest.mark.asyncio
    async def test_facts_context_resource(self, store):
        """Test reading brain://facts resource."""
        from oxmemory.core.models import MemoryType
        store.add("Test fact", MemoryType.FACT, ["test"])
        
        from oxmemory.mcp.resources import get_facts_context
        
        content = await get_facts_context(store)
        
        assert "Test fact" in content
        assert "Known Facts" in content
    
    @pytest.mark.asyncio
    async def test_decisions_context_resource(self, store):
        """Test reading brain://decisions resource."""
        from oxmemory.core.models import MemoryType
        store.add("Test decision", MemoryType.DECISION)
        
        from oxmemory.mcp.resources import get_decisions_context
        
        content = await get_decisions_context(store)
        
        assert "Test decision" in content
        assert "Past Decisions" in content
    
    @pytest.mark.asyncio
    async def test_full_context_resource(self, store):
        """Test reading brain://full resource."""
        from oxmemory.mcp.resources import get_full_context
        
        content = await get_full_context(store)
        
        # Should contain brain, facts, and decisions sections
        assert "Project Brain" in content or "Test Project" in content


class TestMemoryPersistence:
    """Tests for memory persistence across server restarts."""
    
    def test_memories_persist_across_store_instances(self, temp_project):
        """Memories are persisted and readable by new store instances."""
        from oxmemory.core.models import MemoryType
        
        # Create first store and add memory
        _, store1 = create_server(temp_project)
        store1.add("Persistent memory", MemoryType.FACT, ["persistence"])
        
        # Create second store (simulating restart)
        _, store2 = create_server(temp_project)
        
        # Memory should be readable
        memories = store2.list_memories()
        assert len(memories) == 1
        assert memories[0].content == "Persistent memory"


class TestHTTPServer:
    """Tests for HTTP server functionality."""
    
    def test_create_app(self, temp_project):
        """HTTP app can be created."""
        from oxmemory.mcp.http_server import create_app
        
        app = create_app(temp_project)
        
        assert app is not None
        assert app.title == "0xMemory MCP Server"
    
    def test_health_endpoint_exists(self, temp_project):
        """Health endpoint is registered."""
        from oxmemory.mcp.http_server import create_app
        
        app = create_app(temp_project)
        
        # Check routes
        routes = [r.path for r in app.routes]
        assert "/health" in routes
        assert "/sse" in routes
        assert "/messages" in routes


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_recall_empty_store(self, temp_project):
        """Recall on empty store returns empty list."""
        _, store = create_server(temp_project)
        
        from oxmemory.mcp.tools import handle_recall
        
        result = await handle_recall(
            store=store,
            query="anything",
            limit=5,
            types=None,
        )
        
        assert "memories" in result
        assert len(result["memories"]) == 0
    
    @pytest.mark.asyncio
    async def test_forget_nonexistent_memory(self, temp_project):
        """Forget nonexistent memory returns not found."""
        _, store = create_server(temp_project)
        
        from oxmemory.mcp.tools import handle_forget
        
        result = await handle_forget(store=store, id="nonexistent-id")
        
        assert result["success"] is False
        assert "not found" in result.get("error", "").lower()
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_memory(self, temp_project):
        """Update nonexistent memory returns not found."""
        _, store = create_server(temp_project)
        
        from oxmemory.mcp.tools import handle_update
        
        result = await handle_update(
            store=store,
            id="nonexistent-id",
            content="New content",
        )
        
        assert result["success"] is False
