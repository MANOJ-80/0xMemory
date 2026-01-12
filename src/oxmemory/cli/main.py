"""Main CLI application for 0xMemory."""

import asyncio
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from oxmemory import __version__
from oxmemory.cli.export import app as export_app
from oxmemory.core.config import (
    brain_exists,
    get_brain_path,
    get_default_config,
    load_config,
    save_config,
)
from oxmemory.core.models import MemoryType
from oxmemory.mcp.server import run_server
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore

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
    version: bool | None = typer.Option(
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
    project_name: str | None = typer.Option(
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
    save_config(config, cwd)

    # Initialize markdown files
    markdown = MarkdownManager(cwd)
    created_files = markdown.initialize_brain(name, description)

    # Auto-update .gitignore if it exists
    gitignore_path = cwd / ".gitignore"
    gitignore_entry = ".0xmemory/.store/"
    gitignore_updated = False

    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
        if gitignore_entry not in gitignore_content:
            # Append the entry
            with open(gitignore_path, "a") as f:
                if not gitignore_content.endswith("\n"):
                    f.write("\n")
                f.write(f"\n# 0xMemory vector store (auto-added)\n{gitignore_entry}\n")
            gitignore_updated = True

    # Success message
    console.print(
        Panel.fit(
            f"[green]✅ Brain initialized![/green]\n\n"
            f"[bold]Project:[/bold] {name}\n"
            f"[bold]Location:[/bold] {brain_path}\n\n"
            f"[dim]Created files:[/dim]",
            title="🧠 0xMemory",
            border_style="cyan",
        )
    )

    for label, path in created_files.items():
        console.print(f"  📄 {path.relative_to(cwd)}")

    if gitignore_updated:
        console.print(f"  📝 Updated [cyan].gitignore[/cyan] (added {gitignore_entry})")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Edit [cyan].0xmemory/brain.md[/cyan] with your project context")
    console.print("  2. Run [cyan]0xmemory serve[/cyan] to start the MCP server")
    console.print("  3. Configure your AI client (Claude, Gemini, Cursor) to use it")


@app.command()
def serve(
    project_dir: Path | None = typer.Argument(
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
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug logging (verbose output)",
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
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)

    if transport == TransportMode.STDIO:
        # Configure debug logging for stdio
        if debug:
            import logging

            logging.basicConfig(level=logging.DEBUG)
            console.print("[yellow]🐛 Debug mode enabled[/yellow]")
        # Run standard MCP server with stdio
        try:
            asyncio.run(run_server(cwd))
        except KeyboardInterrupt:
            pass
    elif transport == TransportMode.HTTP:
        # Run HTTP server
        try:
            from oxmemory.mcp.http_server import run_http_server

            run_http_server(cwd, host=host, port=port, debug=debug)
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
    project_dir: Path | None = typer.Argument(
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
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
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
        table.add_row("Last Updated", info.last_updated.strftime("%Y-%m-%d %H:%M"))

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
    tags: str | None = typer.Option(
        None,
        "--tags",
        help="Comma-separated tags",
    ),
    project_dir: Path | None = typer.Option(
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
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
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
def forget(
    memory_id: str = typer.Argument(
        ...,
        help="Memory ID to delete (e.g., mem-20260112153045)",
    ),
    project_dir: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Delete a memory by its ID.

    To find memory IDs, use '0xmemory search' or '0xmemory status'.

    Examples:
        0xmemory forget mem-20260112153045
        0xmemory forget mem-20260112153045 --force
    """
    cwd = project_dir or Path.cwd()

    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)

    store = MemoryStore(cwd)

    # Check if memory exists first
    memory = store.get(memory_id)
    if not memory:
        console.print(f"[red]❌ Memory not found: {memory_id}[/red]")
        raise typer.Exit(1)

    # Show what will be deleted
    console.print("\n[yellow]Memory to delete:[/yellow]")
    console.print(f"  [dim]ID:[/dim] {memory.id}")
    console.print(f"  [dim]Type:[/dim] {memory.type.value}")
    console.print(
        f"  [dim]Content:[/dim] {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}"
    )

    # Confirm unless --force
    if not force:
        confirm = typer.confirm("\nAre you sure you want to delete this memory?")
        if not confirm:
            console.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit(0)

    # Delete
    success = store.delete(memory_id)

    if success:
        console.print(f"\n[green]✅ Deleted memory: {memory_id}[/green]")
    else:
        console.print(f"[red]❌ Failed to delete memory: {memory_id}[/red]")
        raise typer.Exit(1)


@app.command()
def update(
    memory_id: str = typer.Argument(
        ...,
        help="Memory ID to update",
    ),
    content: str = typer.Argument(
        ...,
        help="New content for the memory",
    ),
    project_dir: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Update an existing memory's content.

    The memory type and tags are preserved; only the content is changed.

    Examples:
        0xmemory update mem-20260112153045 "Updated content here"
    """
    cwd = project_dir or Path.cwd()

    if not brain_exists(cwd):
        console.print(
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
        )
        raise typer.Exit(1)

    store = MemoryStore(cwd)

    # Check if memory exists
    old_memory = store.get(memory_id)
    if not old_memory:
        console.print(f"[red]❌ Memory not found: {memory_id}[/red]")
        raise typer.Exit(1)

    # Show old content
    console.print("\n[yellow]Updating memory:[/yellow]")
    console.print(f"  [dim]ID:[/dim] {memory_id}")
    old_content_preview = old_memory.content[:80] + ("..." if len(old_memory.content) > 80 else "")
    console.print(f"  [dim]Old:[/dim] {old_content_preview}")
    console.print(f"  [dim]New:[/dim] {content[:80]}{'...' if len(content) > 80 else ''}")

    # Update
    updated = store.update(memory_id, content)

    if updated:
        console.print(f"\n[green]✅ Updated memory: {memory_id}[/green]")
    else:
        console.print(f"[red]❌ Failed to update memory: {memory_id}[/red]")
        raise typer.Exit(1)


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
    type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by memory type",
    ),
    project_dir: Path | None = typer.Option(
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
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
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
    project_dir: Path | None = typer.Option(
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
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
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
        console.print(f"\n[dim]Config file: {get_brain_path(cwd) / 'config.yaml'}[/dim]")
    else:
        console.print("Use [cyan]--show[/cyan] to view configuration.")
        console.print("Edit [cyan].0xmemory/config.yaml[/cyan] directly to modify.")


@app.command()
def rebuild(
    project_dir: Path | None = typer.Option(
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
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
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
    project_dir: Path | None = typer.Option(
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
            f"[red]❌ No brain found at {cwd}[/red]\nRun [cyan]0xmemory init[/cyan] first."
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
            "[red]❌ Extraction module not available.[/red]\nInstall litellm: pip install litellm"
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
        for learning in result.learnings:
            tags = " ".join(f"`{t}`" for t in learning.get("tags", []))
            console.print(f"  • {learning['content']} {tags}")

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


@app.command()
def doctor(
    project_dir: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Run health checks on the brain configuration.

    Validates:
    - Config file syntax (YAML)
    - Vector DB connectivity
    - LLM provider availability
    - Memory file integrity
    - Required directories

    Examples:
        0xmemory doctor
        0xmemory doctor --dir /path/to/project
    """
    import os

    import yaml

    cwd = project_dir or Path.cwd()
    brain_path = get_brain_path(cwd)

    console.print(
        Panel.fit(
            "[bold]Running health checks...[/bold]",
            title="🩺 0xMemory Doctor",
            border_style="cyan",
        )
    )

    checks = []
    all_passed = True

    # Check 1: Brain directory exists
    brain_exists_check = brain_path.exists()
    checks.append(("Brain directory (.0xmemory/)", brain_exists_check, None))
    if not brain_exists_check:
        all_passed = False
        console.print("\n[red]❌ Brain not initialized. Run '0xmemory init' first.[/red]")
        _print_doctor_summary(checks, all_passed)
        raise typer.Exit(1)

    # Check 2: Config file syntax
    config_ok = True
    config_error = None
    config_path = brain_path / "config.yaml"
    if config_path.exists():
        try:
            with open(config_path) as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            config_ok = False
            config_error = str(e)
            all_passed = False
    else:
        config_ok = False
        config_error = "File not found"
        all_passed = False
    checks.append(("Config file syntax", config_ok, config_error))

    # Check 3: brain.md exists
    brain_md_path = brain_path / "brain.md"
    brain_md_ok = brain_md_path.exists()
    checks.append(("brain.md exists", brain_md_ok, None if brain_md_ok else "File not found"))
    if not brain_md_ok:
        all_passed = False

    # Check 4: Memory directory
    memory_dir = brain_path / "memory"
    memory_dir_ok = memory_dir.exists() and memory_dir.is_dir()
    checks.append(
        ("Memory directory", memory_dir_ok, None if memory_dir_ok else "Directory not found")
    )
    if not memory_dir_ok:
        all_passed = False

    # Check 5: Memory file integrity
    memory_files = ["facts.md", "decisions.md", "learnings.md", "preferences.md"]
    memory_integrity_ok = True
    memory_error = None
    for mf in memory_files:
        mf_path = memory_dir / mf
        if mf_path.exists():
            try:
                content = mf_path.read_text()
                # Basic check: should have a header
                if not content.strip().startswith("#"):
                    memory_integrity_ok = False
                    memory_error = f"{mf} missing header"
                    break
            except Exception as e:
                memory_integrity_ok = False
                memory_error = f"{mf}: {e}"
                break
    checks.append(("Memory file integrity", memory_integrity_ok, memory_error))
    if not memory_integrity_ok:
        all_passed = False

    # Check 6: Vector DB (ChromaDB)
    vector_ok = True
    vector_error = None
    try:
        import chromadb

        # Try to connect to the store
        store_path = brain_path / ".store" / "chroma"
        if store_path.exists():
            client = chromadb.PersistentClient(path=str(store_path))
            # Just test we can list collections
            client.list_collections()
        else:
            vector_error = "Store not yet created (will be created on first use)"
    except ImportError:
        vector_ok = False
        vector_error = "chromadb not installed (pip install chromadb)"
        all_passed = False
    except Exception as e:
        vector_ok = False
        vector_error = str(e)
        all_passed = False
    checks.append(("Vector DB (ChromaDB)", vector_ok, vector_error))

    # Check 7: LLM Providers
    llm_available = []
    llm_missing = []

    # Check Ollama
    ollama_host = os.environ.get("OLLAMA_API_BASE", "http://localhost:11434")
    try:
        import urllib.request

        req = urllib.request.Request(f"{ollama_host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                llm_available.append("Ollama")
    except Exception:
        llm_missing.append("Ollama (not running)")

    # Check Groq
    if os.environ.get("GROQ_API_KEY"):
        llm_available.append("Groq")
    else:
        llm_missing.append("Groq (GROQ_API_KEY not set)")

    # Check Gemini
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        llm_available.append("Gemini")
    else:
        llm_missing.append("Gemini (GEMINI_API_KEY not set)")

    # Check OpenRouter
    if os.environ.get("OPENROUTER_API_KEY"):
        llm_available.append("OpenRouter")
    else:
        llm_missing.append("OpenRouter (OPENROUTER_API_KEY not set)")

    llm_ok = len(llm_available) > 0
    checks.append(("LLM Provider", llm_ok, None if llm_ok else "No providers configured"))

    # Print results
    _print_doctor_summary(checks, all_passed)

    # Additional info
    if llm_available:
        console.print(f"\n[green]Available LLM providers:[/green] {', '.join(llm_available)}")
    if llm_missing:
        console.print(f"[dim]Inactive providers: {', '.join(llm_missing)}[/dim]")

    if all_passed:
        console.print("\n[green]✅ All checks passed! Your brain is healthy.[/green]")
    else:
        console.print("\n[yellow]⚠️  Some checks failed. See above for details.[/yellow]")
        raise typer.Exit(1)


def _print_doctor_summary(checks: list, all_passed: bool) -> None:
    """Print doctor check summary as a table."""
    table = Table(title="Health Check Results", border_style="cyan")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details", style="dim")

    for name, passed, error in checks:
        status = "[green]✓ Pass[/green]" if passed else "[red]✗ Fail[/red]"
        details = error or ""
        table.add_row(name, status, details)

    console.print(table)


if __name__ == "__main__":
    app()
