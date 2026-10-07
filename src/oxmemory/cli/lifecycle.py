"""Commit evidence and memory lifecycle CLI, emitting reviewable JSON."""

import json
from pathlib import Path

import typer

from oxmemory.core.models import MemoryType
from oxmemory.storage.memory_store import MemoryStore

app = typer.Typer(help="Manage code-linked memory and preserved decision history.")


def invoke(action):
    try:
        result = action()
        if hasattr(result, "model_dump"):
            result = result.model_dump(mode="json")
        typer.echo(json.dumps(result, indent=2, ensure_ascii=True))
    except (ValueError, OSError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


def store_at(project: Path) -> MemoryStore:
    store = MemoryStore(project)
    if not store.is_initialized():
        raise ValueError("Run 0xmemory init in the repository root first")
    return store


@app.command("remember")
def remember(content: str, file: list[str] = typer.Option([], "--file"),
             symbol: list[str] = typer.Option([], "--symbol"), commit: str = "HEAD",
             type: MemoryType = MemoryType.DECISION, project: Path = Path(".")):
    """Save a decision with evidence at a Git commit."""
    invoke(lambda: store_at(project).add(content, type, file_paths=file, symbols=symbol,
                                         commit_sha=commit))


@app.command("observe")
def observe(commit: str = "HEAD", project: Path = Path(".")):
    """Explicitly inspect committed changes; no Git hook is installed."""
    invoke(lambda: store_at(project).observe_commit(commit))


@app.command("verify")
def verify(id: str, note: str = typer.Option(..., "--note"), commit: str = "HEAD",
           project: Path = Path(".")):
    """Confirm an existing memory after reviewing its supporting code."""
    invoke(lambda: store_at(project).verify(id, commit, note))


@app.command("supersede")
def supersede(id: str, content: str, note: str = typer.Option(..., "--note"),
              commit: str = "HEAD", file: list[str] = typer.Option([], "--file"),
              project: Path = Path(".")):
    """Replace a decision and retain its original evidence."""
    invoke(lambda: store_at(project).supersede(id, content, commit, note, file or None))


@app.command("recall")
def recall(query: str, file: list[str] = typer.Option([], "--file"),
           history: bool = False, token_budget: int = 1500, project: Path = Path(".")):
    """Retrieve current decisions, with evidence and ranking explanations."""
    invoke(lambda: store_at(project).recall_context(
        query, file_paths=file, include_history=history, token_budget=token_budget,
    ))


@app.command("inspect")
def inspect(project: Path = Path(".")):
    """List all lifecycle states including stale and superseded decisions."""
    invoke(lambda: [
        m.model_dump(mode="json") for m in store_at(project).list_memories(limit=10000)
    ])
