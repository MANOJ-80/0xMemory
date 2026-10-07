"""MCP Server implementation for 0xMemory.

Implements the Model Context Protocol server using stdio transport.
"""

import json
import logging
from pathlib import Path
from typing import Any

import mcp.types as types
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
    store = MemoryStore(project_dir)

    # -------------------------------------------------------------------------
    # Tool definitions
    # -------------------------------------------------------------------------

    async def list_tools() -> list[Tool]:
        """List available tools."""
        definitions = [
            Tool(
                name="remember",
                description="Store a new memory (fact, decision, learning, or preference). "
                "Use this to save important information from the conversation.",
                input_schema={
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
                input_schema={
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
                input_schema={
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
                input_schema={
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
                input_schema={
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
                input_schema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="extract",
                description="Extract facts, decisions, and learnings from a conversation "
                "using LLM. Requires Ollama, Groq, or Gemini.",
                input_schema={
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

        array = {"type": "array", "items": {"type": "string"}}
        for tool in definitions:
            props = tool.input_schema["properties"]
            if tool.name in {"remember", "recall"}:
                props["file_paths"] = dict(array, description="Repository-relative evidence files")
                props["symbols"] = dict(array, description="Relevant function/class names")
            if tool.name == "remember":
                props["commit_sha"] = {"type": "string", "description": "Evidence commit"}
            if tool.name == "recall":
                props["include_history"] = {"type": "boolean", "default": False}
                props["token_budget"] = {"type": "integer", "minimum": 1, "default": 1500}
        for name, description, properties, required in [
            ("observe_commit", "Mark memories affected by committed file changes as needing verification.",
             {"commit": {"type": "string", "default": "HEAD"}}, []),
            ("verify_memory", "Record your explicit verification of a memory against a commit. Read its evidence first.",
             {"id": {"type": "string"}, "commit": {"type": "string"}, "note": {"type": "string"}},
             ["id", "commit", "note"]),
            ("supersede_memory", "Replace a decision after checking the new evidence; preserve the original in history.",
             {"id": {"type": "string"}, "content": {"type": "string"}, "commit": {"type": "string"},
              "note": {"type": "string"}, "file_paths": array}, ["id", "content", "commit", "note"]),
        ]:
            definitions.append(Tool(name=name, description=description, input_schema={
                "type": "object", "properties": properties, "required": required,
            }))
        return definitions

    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "observe_commit":
                result = store.observe_commit(arguments.get("commit", "HEAD"))
            elif name == "verify_memory":
                result = store.verify(arguments["id"], arguments["commit"], arguments["note"]).model_dump(mode="json")
            elif name == "supersede_memory":
                result = store.supersede(arguments["id"], arguments["content"], arguments["commit"],
                                         arguments["note"], arguments.get("file_paths")).model_dump(mode="json")
            elif name == "remember":
                result = await handle_remember(
                    store=store,
                    content=arguments["content"],
                    type=arguments.get("type", "fact"),
                    tags=arguments.get("tags"),
                    source=arguments.get("source", "conversation"),
                    file_paths=arguments.get("file_paths"),
                    symbols=arguments.get("symbols"),
                    commit_sha=arguments.get("commit_sha"),
                )
            elif name == "recall":
                result = await handle_recall(
                    store=store,
                    query=arguments["query"],
                    limit=arguments.get("limit", 5),
                    types=arguments.get("types"),
                    file_paths=arguments.get("file_paths"),
                    symbols=arguments.get("symbols"),
                    include_history=arguments.get("include_history", False),
                    token_budget=arguments.get("token_budget", 1500),
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

    async def list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="brain://context",
                name="Project Context",
                description="Main project brain (brain.md)",
                mime_type="text/markdown",
            ),
            Resource(
                uri="brain://facts",
                name="Known Facts",
                description="All extracted and stored facts",
                mime_type="text/markdown",
            ),
            Resource(
                uri="brain://decisions",
                name="Decision Log",
                description="Past decisions and their rationale",
                mime_type="text/markdown",
            ),
            Resource(
                uri="brain://full",
                name="Full Context",
                description="Combined brain, facts, and decisions",
                mime_type="text/markdown",
            ),
        ]

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

    async def on_list_tools(ctx, params):
        return types.ListToolsResult(tools=await list_tools())

    async def on_call_tool(ctx, params):
        return types.CallToolResult(content=await call_tool(params.name, params.arguments or {}))

    async def on_list_resources(ctx, params):
        return types.ListResourcesResult(resources=await list_resources())

    async def on_read_resource(ctx, params):
        return types.ReadResourceResult(contents=[types.TextResourceContents(
            uri=params.uri, mime_type="text/markdown", text=await read_resource(str(params.uri)),
        )])

    async def on_list_prompts(ctx, params):
        return types.ListPromptsResult(prompts=await list_prompts())

    async def on_get_prompt(ctx, params):
        return await get_prompt(params.name, params.arguments)

    server = Server(
        "0xmemory", on_list_tools=on_list_tools, on_call_tool=on_call_tool,
        on_list_resources=on_list_resources, on_read_resource=on_read_resource,
        on_list_prompts=on_list_prompts, on_get_prompt=on_get_prompt,
    )
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
    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options(),
            )
    finally:
        store.close()
