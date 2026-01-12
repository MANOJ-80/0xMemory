"""MCP Server implementation for 0xMemory.

Implements the Model Context Protocol server using stdio transport.
"""

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    TextContent,
    Tool,
)

from oxmemory.mcp.resources import (
    get_brain_context,
    get_decisions_context,
    get_facts_context,
    get_full_context,
)
from oxmemory.mcp.tools import (
    handle_extract,
    handle_forget,
    handle_list,
    handle_recall,
    handle_remember,
    handle_status,
    handle_update,
)
from oxmemory.storage.memory_store import MemoryStore

logger = logging.getLogger(__name__)


def create_server(project_dir: Path | None = None) -> tuple[Server, MemoryStore]:
    """Create an MCP server instance.

    Args:
        project_dir: Project directory. Defaults to current directory.

    Returns:
        Tuple of (Server, MemoryStore).
    """
    server = Server("0xmemory")
    store = MemoryStore(project_dir)

    # -------------------------------------------------------------------------
    # Tool definitions
    # -------------------------------------------------------------------------

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="remember",
                description="Store a new memory (fact, decision, learning, or preference). "
                "Use this to save important information from the conversation.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The memory content to store",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["fact", "decision", "learning", "preference"],
                            "description": "Type of memory",
                            "default": "fact",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional categorization tags",
                        },
                        "source": {
                            "type": "string",
                            "description": "Where this memory came from",
                            "default": "conversation",
                        },
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="recall",
                description="Search memories by meaning/content. "
                "Use this to find relevant past information.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 5,
                        },
                        "types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by memory types",
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="list",
                description="List all stored memories, optionally filtered by type.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": ["fact", "decision", "learning", "preference"],
                            "description": "Filter by memory type",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 20,
                        },
                    },
                },
            ),
            Tool(
                name="forget",
                description="Remove a memory by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Memory ID to remove",
                        },
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="update",
                description="Update an existing memory's content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Memory ID to update",
                        },
                        "content": {
                            "type": "string",
                            "description": "New content for the memory",
                        },
                    },
                    "required": ["id", "content"],
                },
            ),
            Tool(
                name="status",
                description="Get brain statistics - number of facts, decisions, etc.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="extract",
                description="Extract facts, decisions, and learnings from a conversation "
                "using LLM. Requires Ollama, Groq, or Gemini.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "conversation": {
                            "type": "string",
                            "description": "The conversation text to analyze",
                        },
                        "auto_save": {
                            "type": "boolean",
                            "description": "Whether to automatically save extracted memories",
                            "default": True,
                        },
                    },
                    "required": ["conversation"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "remember":
                result = await handle_remember(
                    store=store,
                    content=arguments["content"],
                    type=arguments.get("type", "fact"),
                    tags=arguments.get("tags"),
                    source=arguments.get("source", "conversation"),
                )
            elif name == "recall":
                result = await handle_recall(
                    store=store,
                    query=arguments["query"],
                    limit=arguments.get("limit", 5),
                    types=arguments.get("types"),
                )
            elif name == "list":
                result = await handle_list(
                    store=store,
                    type=arguments.get("type"),
                    limit=arguments.get("limit", 20),
                )
            elif name == "forget":
                result = await handle_forget(
                    store=store,
                    id=arguments["id"],
                )
            elif name == "update":
                result = await handle_update(
                    store=store,
                    id=arguments["id"],
                    content=arguments["content"],
                )
            elif name == "status":
                result = await handle_status(store)
            elif name == "extract":
                result = await handle_extract(
                    store=store,
                    conversation=arguments["conversation"],
                    auto_save=arguments.get("auto_save", True),
                )
            else:
                result = {"error": f"Unknown tool: {name}"}

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.exception(f"Error in tool {name}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    # -------------------------------------------------------------------------
    # Resource definitions
    # -------------------------------------------------------------------------

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="brain://context",
                name="Project Context",
                description="Main project brain (brain.md)",
                mimeType="text/markdown",
            ),
            Resource(
                uri="brain://facts",
                name="Known Facts",
                description="All extracted and stored facts",
                mimeType="text/markdown",
            ),
            Resource(
                uri="brain://decisions",
                name="Decision Log",
                description="Past decisions and their rationale",
                mimeType="text/markdown",
            ),
            Resource(
                uri="brain://full",
                name="Full Context",
                description="Combined brain, facts, and decisions",
                mimeType="text/markdown",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a resource by URI."""
        logger.info(f"Reading resource: {str(uri)!r}")

        # Normalize URI: strip trailing slash and handle triple slash
        normalized_uri = str(uri).strip().rstrip("/")
        if normalized_uri.startswith("brain:///"):
            normalized_uri = "brain://" + normalized_uri[9:]

        if normalized_uri == "brain://context":
            return await get_brain_context(store)
        elif normalized_uri == "brain://facts":
            return await get_facts_context(store)
        elif normalized_uri == "brain://decisions":
            return await get_decisions_context(store)
        elif normalized_uri == "brain://full":
            return await get_full_context(store)
        else:
            logger.error(f"Unknown resource URI: {uri!r} (normalized: {normalized_uri!r})")
            raise ValueError(f"Unknown resource: {uri}")

    # -------------------------------------------------------------------------
    # Prompt definitions
    # -------------------------------------------------------------------------

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """List available prompts."""
        return [
            Prompt(
                name="project_context",
                description="Get full project context for any task",
                arguments=[],
            ),
            Prompt(
                name="extract_knowledge",
                description="Extract facts and decisions from a conversation",
                arguments=[
                    PromptArgument(
                        name="conversation",
                        description="The conversation to analyze",
                        required=True,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
        """Get a prompt by name."""
        if name == "project_context":
            context = await get_full_context(store)
            return GetPromptResult(
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"Here is the project context:\n\n{context}",
                        ),
                    ),
                ],
            )
        elif name == "extract_knowledge":
            conversation = arguments.get("conversation", "") if arguments else ""
            return GetPromptResult(
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"""Review this conversation and extract:
1. New facts about the project (technical details, configurations, etc.)
2. Decisions made with their rationale
3. Lessons learned or gotchas

For each item, use the 'remember' tool to store it.

Conversation:
{conversation}""",
                        ),
                    ),
                ],
            )
        else:
            raise ValueError(f"Unknown prompt: {name}")

    return server, store


async def run_server(project_dir: Path | None = None) -> None:
    """Run the MCP server with stdio transport.

    Args:
        project_dir: Project directory. Defaults to current directory.
    """
    server, store = create_server(project_dir)

    # Check if brain exists
    if not store.is_initialized():
        logger.warning(
            f"Brain not initialized in {project_dir or Path.cwd()}. Run '0xmemory init' first."
        )

    # Run with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
