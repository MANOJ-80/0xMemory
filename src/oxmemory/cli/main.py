"""Main CLI application for 0xMemory."""

import asyncio
from pathlib import Path
from typing import Optional
from enum import Enum

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from oxmemory import __version__
from oxmemory.core.config import (
    get_brain_path, 
    get_default_config, 
    save_config, 
    brain_exists,
    load_config,
)
from oxmemory.core.models import MemoryType
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore
from oxmemory.mcp.server import run_server
from oxmemory.cli.export import app as export_app

app = typer.Typer(
    name="0xmemory",
    help="🧠 Cross-LLM memory layer for AI agents",
    add_completion=True,
    rich_markup_mode="rich",
)

# Register export command
app.add_typer(export_app, name="export")

console = Console()


class TransportMode(str, Enum):
    STDIO = "stdio"
    HTTP = "http"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"0xMemory version: [cyan]{__version__}[/cyan]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """🧠 0xMemory - Cross-LLM memory layer for AI agents.
    
    Transforms your project into a living brain with persistent,
    human-editable memory that works across Claude, Gemini, and Cursor.
    """
    pass


@app.command()
def init(
    project_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="Project name (defaults to directory name)",
    ),
    description: str = typer.Option(
        "",
        "--description",
        "-d",
        help="Project description",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing brain",
    ),
) -> None:
    """Initialize a new brain in the current directory.
    
    Creates the .0xmemory/ directory with:
    - brain.md - Main project context (edit this!)
    - memory/ - Facts, decisions, learnings
    - config.yaml - Configuration
    """
    cwd = Path.cwd()
    brain_path = get_brain_path(cwd)
    
    if brain_path.exists() and not force:
        console.print(
            f"[yellow]⚠️  Brain already exists at {brain_path}[/yellow]\n"
            "Use --force to reinitialize."
        )
        raise typer.Exit(1)
    
    # Determine project name
    name = project_name or cwd.name
    
    # Create config
    config = get_default_config(name)
    config.project.description = description
    
    # Save config
    config_path = save_config(config, cwd)
    
    # Initialize markdown files
    markdown = MarkdownManager(cwd)
    created_files = markdown.initialize_brain(name, description)
    
    # Success message
    console.print(Panel.fit(
        f"[green]✅ Brain initialized![/green]\n\n"
        f"[bold]Project:[/bold] {name}\n"
        f"[bold]Location:[/bold] {brain_path}\n\n"
        f"[dim]Created files:[/dim]",
        title="🧠 0xMemory",
        border_style="cyan",
    ))
    
    for label, path in created_files.items():
        console.print(f"  📄 {path.relative_to(cwd)}")
    
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print("  1. Edit [cyan].0xmemory/brain.md[/cyan] with your project context")
    console.print("  2. Run [cyan]0xmemory serve[/cyan] to start the MCP server")
    console.print("  3. Configure your AI client (Claude, Gemini, Cursor) to use it")


@app.command()
def serve(
    project_dir: Optional[Path] = typer.Argument(
        None,
        help="Project directory (defaults to current)",
    ),
    transport: TransportMode = typer.Option(
        TransportMode.STDIO,
        "--transport",
        "-t",
        help="Transport mode (stdio or http)",
    ),
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind to (http only)",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to listen on (http only)",
    ),
) -> None:
    """Start the MCP server for AI clients.
    
    Supports two transport modes:
    1. stdio (default): For local clients (Claude Desktop)
    2. http (SSE): For remote clients (Cursor, etc.)
    
    Examples:
        0xmemory serve
        0xmemory serve --transport http --port 9000
    """
    cwd = project_dir or Path.cwd()
    
    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\n"
            "Run [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)
    
    if transport == TransportMode.STDIO:
        # Run standard MCP server with stdio
        try:
            asyncio.run(run_server(cwd))
        except KeyboardInterrupt:
            pass
    elif transport == TransportMode.HTTP:
        # Run HTTP server
        try:
            from oxmemory.mcp.http_server import run_http_server
            run_http_server(cwd, host=host, port=port)
        except ImportError:
            console.print(
                "[red]❌ HTTP server dependencies missing.[/red]\n"
                "Install with: [cyan]pip install fastapi uvicorn[/cyan]"
            )
            raise typer.Exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped.[/yellow]")


@app.command()
def status(
    project_dir: Optional[Path] = typer.Argument(
        None,
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Show brain statistics.
    
    Displays the number of facts, decisions, learnings, and
    other information about the brain.
    """
    cwd = project_dir or Path.cwd()
    
    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\n"
            "Run [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)
    
    store = MemoryStore(cwd)
    info = store.get_brain_info()
    
    # Create status table
    table = Table(title="🧠 Brain Status", border_style="cyan")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    table.add_row("Project", info.project_name)
    table.add_row("Location", info.brain_path)
    table.add_row("", "")
    table.add_row("📚 Facts", str(info.facts_count))
    table.add_row("🎯 Decisions", str(info.decisions_count))
    table.add_row("💡 Learnings", str(info.learnings_count))
    table.add_row("⚙️  Preferences", str(info.preferences_count))
    table.add_row("🧵 Sessions", str(info.sessions_count))
    table.add_row("", "")
    table.add_row("Total Memories", f"[bold]{info.total_memories}[/bold]")
    
    if info.last_updated:
        table.add_row(
            "Last Updated", 
            info.last_updated.strftime("%Y-%m-%d %H:%M")
        )
    
    console.print(table)


@app.command()
def add(
    content: str = typer.Argument(
        ...,
        help="Memory content to add",
    ),
    type: str = typer.Option(
        "fact",
        "--type",
        "-t",
        help="Memory type: fact, decision, learning, preference",
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        help="Comma-separated tags",
    ),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Manually add a memory to the brain.
    
    Examples:
        0xmemory add "The API uses port 3000" --type fact --tags api,config
        0xmemory add "Chose PostgreSQL over MongoDB" --type decision
    """
    cwd = project_dir or Path.cwd()
    
    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\n"
            "Run [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)
    
    # Parse type
    try:
        memory_type = MemoryType(type.lower())
    except ValueError:
        console.print(
            f"[red]❌ Invalid type: {type}[/red]\n"
            "Must be one of: fact, decision, learning, preference"
        )
        raise typer.Exit(1)
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    # Add memory
    store = MemoryStore(cwd)
    memory = store.add(
        content=content,
        memory_type=memory_type,
        tags=tag_list,
        source="cli",
    )
    
    # Success message
    tags_str = ", ".join(f"`{t}`" for t in tag_list) if tag_list else "none"
    console.print(
        f"[green]✅ Added {memory_type.value}[/green]\n"
        f"[dim]ID:[/dim] {memory.id}\n"
        f"[dim]Tags:[/dim] {tags_str}\n"
        f"[dim]Content:[/dim] {content[:80]}{'...' if len(content) > 80 else ''}"
    )


@app.command()
def search(
    query: str = typer.Argument(
        ...,
        help="Search query",
    ),
    limit: int = typer.Option(
        5,
        "--limit",
        "-l",
        help="Maximum number of results",
    ),
    type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by memory type",
    ),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Search through stored memories.
    
    Uses keyword matching in Phase 1, semantic search in Phase 2.
    
    Examples:
        0xmemory search "authentication"
        0xmemory search "database" --type fact
    """
    cwd = project_dir or Path.cwd()
    
    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\n"
            "Run [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)
    
    # Parse type filter
    memory_types = None
    if type:
        try:
            memory_types = [MemoryType(type.lower())]
        except ValueError:
            console.print(f"[yellow]⚠️  Unknown type: {type}, searching all[/yellow]")
    
    store = MemoryStore(cwd)
    results = store.search(query, limit=limit, memory_types=memory_types)
    
    if not results:
        console.print(f"[yellow]No memories found matching: {query}[/yellow]")
        return
    
    console.print(f"[green]Found {len(results)} memories:[/green]\n")
    
    for i, memory in enumerate(results, 1):
        tags_str = " ".join(f"`{t}`" for t in memory.tags) if memory.tags else ""
        console.print(
            f"[bold]{i}.[/bold] [{memory.type.value}] {tags_str}\n"
            f"   {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}\n"
            f"   [dim]ID: {memory.id} | {memory.created_at.strftime('%Y-%m-%d')}[/dim]\n"
        )


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current configuration",
    ),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """View or modify configuration.
    
    Examples:
        0xmemory config --show
    """
    cwd = project_dir or Path.cwd()
    
    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\n"
            "Run [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)
    
    if show:
        cfg = load_config(cwd)
        
        table = Table(title="⚙️  Configuration", border_style="cyan")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Version", cfg.version)
        table.add_row("Project Name", cfg.project.name)
        table.add_row("Project Description", cfg.project.description or "[dim]not set[/dim]")
        table.add_row("", "")
        table.add_row("Embedding Model", cfg.embeddings.model)
        table.add_row("Max Facts", str(cfg.memory.max_facts))
        table.add_row("Decay Enabled", str(cfg.memory.decay_enabled))
        table.add_row("", "")
        table.add_row("Git Auto-Commit", str(cfg.git.auto_commit))
        table.add_row("Commit Prefix", cfg.git.commit_prefix)
        
        console.print(table)
        console.print(
            f"\n[dim]Config file: {get_brain_path(cwd) / 'config.yaml'}[/dim]"
        )
    else:
        console.print("Use [cyan]--show[/cyan] to view configuration.")
        console.print("Edit [cyan].0xmemory/config.yaml[/cyan] directly to modify.")


@app.command()
def rebuild(
    project_dir: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Rebuild the vector index from Markdown files.
    
    Use this if the vector store becomes corrupted or out of sync
    with the Markdown files. The Markdown files are always the
    source of truth.
    """
    cwd = project_dir or Path.cwd()
    
    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\n"
            "Run [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)
    
    console.print("[yellow]🔄 Rebuilding vector index...[/yellow]")
    
    store = MemoryStore(cwd)
    result = store.rebuild_vectors()
    
    if "error" in result:
        console.print(f"[red]❌ {result['error']}[/red]")
        raise typer.Exit(1)
    
    console.print(
        f"[green]✅ Rebuilt vector index![/green]\n"
        f"[dim]Total indexed:[/dim] {result['rebuilt']}\n"
        f"  📚 Facts: {result['facts']}\n"
        f"  🎯 Decisions: {result['decisions']}\n"
        f"  💡 Learnings: {result['learnings']}\n"
        f"  ⚙️  Preferences: {result['preferences']}"
    )


@app.command()
def extract(
    text: str = typer.Argument(
        ...,
        help="Text or conversation to extract knowledge from",
    ),
    no_save: bool = typer.Option(
        False,
        "--no-save",
        help="Don't save extracted memories, just show them",
    ),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Extract facts, decisions, and learnings from text using LLM.
    
    Requires an LLM provider (Ollama, Groq, or Gemini) to be configured.
    
    Examples:
        0xmemory extract "We decided to use PostgreSQL because..."
        0xmemory extract "$(cat conversation.txt)" --no-save
    """
    cwd = project_dir or Path.cwd()
    
    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\n"
            "Run [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)
    
    console.print("[yellow]🔍 Extracting knowledge...[/yellow]")
    
    async def run_extraction():
        from oxmemory.extraction import KnowledgeExtractor
        
        extractor = KnowledgeExtractor()
        
        if not extractor.is_available():
            console.print(
                "[red]❌ No LLM provider available.[/red]\n"
                "Configure one of:\n"
                "  - Ollama (local): ollama run llama3.2:3b\n"
                "  - Groq (free): export GROQ_API_KEY=...\n"
                "  - Gemini (free): export GEMINI_API_KEY=..."
            )
            raise typer.Exit(1)
        
        result = await extractor.extract(text)
        
        if result.error:
            console.print(f"[red]❌ Extraction failed: {result.error}[/red]")
            raise typer.Exit(1)
        
        return result, extractor
    
    try:
        result, extractor = asyncio.run(run_extraction())
    except ImportError:
        console.print(
            "[red]❌ Extraction module not available.[/red]\n"
            "Install litellm: pip install litellm"
        )
        raise typer.Exit(1)
    
    # Display results
    total = len(result.facts) + len(result.decisions) + len(result.learnings)
    
    if total == 0:
        console.print("[yellow]No knowledge worth extracting found.[/yellow]")
        return
    
    console.print(f"\n[green]Found {total} items:[/green]\n")
    
    if result.facts:
        console.print("[bold]📚 Facts:[/bold]")
        for f in result.facts:
            tags = " ".join(f"`{t}`" for t in f.get("tags", []))
            console.print(f"  • {f['content']} {tags}")
    
    if result.decisions:
        console.print("\n[bold]🎯 Decisions:[/bold]")
        for d in result.decisions:
            tags = " ".join(f"`{t}`" for t in d.get("tags", []))
            console.print(f"  • {d['content']} {tags}")
    
    if result.learnings:
        console.print("\n[bold]💡 Learnings:[/bold]")
        for l in result.learnings:
            tags = " ".join(f"`{t}`" for t in l.get("tags", []))
            console.print(f"  • {l['content']} {tags}")
    
    # Save if requested
    if not no_save:
        store = MemoryStore(cwd)
        memories = extractor.extraction_to_memories(result)
        for memory in memories:
            store.add(
                content=memory.content,
                memory_type=memory.type,
                tags=memory.tags,
                source="extraction",
                salience=memory.salience,
            )
        console.print(f"\n[green]✅ Saved {len(memories)} memories[/green]")


if __name__ == "__main__":
    app()
