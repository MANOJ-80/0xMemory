"""HTTP Server implementation for 0xMemory (FastAPI + SSE)."""

import logging
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

from oxmemory.mcp.server import create_server
from oxmemory.core.config import brain_exists

logger = logging.getLogger(__name__)


def create_app(project_dir: Optional[Path] = None) -> FastAPI:
    """Create FastAPI app for MCP server.
    
    Args:
        project_dir: Project directory.
        
    Returns:
        FastAPI application.
    """
    server, store = create_server(project_dir)
    
    # Check if brain exists
    if not store.is_initialized():
        logger.warning(
            f"Brain not initialized in {project_dir or Path.cwd()}. "
            "Some tools may not work."
        )

    # Create SSE transport
    # Create SSE transport
    # Create SSE transport
    transport = SseServerTransport("/messages")
    
    class SSEHandler:
        """Raw ASGI handler for SSE."""
        async def __call__(self, scope, receive, send):
            async with transport.connect_sse(
                scope, 
                receive, 
                send
            ) as streams:
                await server.run(
                    streams[0], 
                    streams[1], 
                    server.create_initialization_options()
                )

    class MessagesHandler:
        """Raw ASGI handler for Messages."""
        async def __call__(self, scope, receive, send):
            await transport.handle_post_message(
                scope, 
                receive, 
                send
            )

    app = FastAPI(
        title="0xMemory MCP Server",
        description="Cross-LLM memory layer for AI agents",
        routes=[
            Route("/sse", endpoint=SSEHandler(), methods=["GET"]),
            Route("/messages", endpoint=MessagesHandler(), methods=["POST"]),
        ]
    )
    
    return app


def run_http_server(
    project_dir: Optional[Path] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
):
    """Run the MCP server with HTTP transport (SSE).
    
    Args:
        project_dir: Project directory.
        host: Host to bind to.
        port: Port to listen on.
    """
    app = create_app(project_dir)
    
    print(f"🧠 0xMemory Server running on http://{host}:{port}")
    print(f"   SSE Endpoint: http://{host}:{port}/sse")
    print("   Press Ctrl+C to stop")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
