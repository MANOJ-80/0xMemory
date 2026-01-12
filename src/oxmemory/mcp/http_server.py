"""HTTP Server implementation for 0xMemory (FastAPI + SSE)."""

import logging
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

from oxmemory import __version__
from oxmemory.mcp.server import create_server
from oxmemory.core.config import brain_exists

logger = logging.getLogger(__name__)


def create_app(project_dir: Optional[Path] = None, debug: bool = False) -> FastAPI:
    """Create FastAPI app for MCP server.
    
    Args:
        project_dir: Project directory.
        debug: Enable debug logging.
        
    Returns:
        FastAPI application.
    """
    server, store = create_server(project_dir)
    
    # Check if brain exists
    brain_initialized = store.is_initialized()
    if not brain_initialized:
        logger.warning(
            f"Brain not initialized in {project_dir or Path.cwd()}. "
            "Some tools may not work."
        )

    # Check vector store availability
    vector_available = False
    try:
        from oxmemory.storage.vector_store import VectorStore
        vector_available = True
    except ImportError:
        pass

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

    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint for load balancers."""
        return JSONResponse({
            "status": "healthy",
            "version": __version__,
            "brain_initialized": brain_initialized,
            "vector_store_available": vector_available,
            "project_dir": str(project_dir or Path.cwd()),
        })

    app = FastAPI(
        title="0xMemory MCP Server",
        description="Cross-LLM memory layer for AI agents",
        version=__version__,
        routes=[
            Route("/sse", endpoint=SSEHandler(), methods=["GET"]),
            Route("/messages", endpoint=MessagesHandler(), methods=["POST"]),
            Route("/health", endpoint=health_check, methods=["GET"]),
        ]
    )
    
    return app


def run_http_server(
    project_dir: Optional[Path] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
):
    """Run the MCP server with HTTP transport (SSE).
    
    Args:
        project_dir: Project directory.
        host: Host to bind to.
        port: Port to listen on.
        debug: Enable debug logging.
    """
    # Configure logging based on debug flag
    log_level = "debug" if debug else "info"
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    app = create_app(project_dir, debug=debug)
    
    print(f"🧠 0xMemory Server running on http://{host}:{port}")
    print(f"   SSE Endpoint: http://{host}:{port}/sse")
    print(f"   Health Check: http://{host}:{port}/health")
    if debug:
        print("   🐛 Debug mode: ENABLED")
    print("   Press Ctrl+C to stop")
    
    uvicorn.run(app, host=host, port=port, log_level=log_level)
