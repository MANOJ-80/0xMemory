"""Commit evidence and memory lifecycle CLI, emitting reviewable JSON."""

import json
from datetime import datetime
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
             type: MemoryType = MemoryType.DECISION, project: Path = Path("."),
             scope: str = "project", scope_id: str | None = None,
             valid_from: datetime | None = typer.Option(None, "--valid-from"),
             valid_to: datetime | None = typer.Option(None, "--valid-to"),
             confidence: float | None = typer.Option(None, "--extraction-confidence", min=0.0, max=1.0),
             claim_confidence: float | None = typer.Option(None, "--claim-confidence", min=0.0, max=1.0),
             claim_subject: str | None = None, claim_predicate: str | None = None,
             claim_value: str | None = None, claim_environment: str | None = None,
             claim_state: str = typer.Option("asserted", help="asserted, proposed, evaluating, adopted, rejected, or unknown")):
    """Save a decision with evidence at a Git commit."""
    invoke(lambda: store_at(project).add(content, type, file_paths=file, symbols=symbol,
                                         commit_sha=commit, scope_type=scope, scope_id=scope_id,
                                         valid_from=valid_from, valid_to=valid_to,
                                         claim_confidence=claim_confidence,
                                         confidence=confidence,
                                         claim_subject=claim_subject, claim_predicate=claim_predicate,
                                         claim_value=claim_value, claim_environment=claim_environment,
                                         claim_state=claim_state))


@app.command("propose")
def propose(content: str, type: MemoryType = MemoryType.LEARNING,
            source: str = "manual-candidate", scope: str = "project",
            scope_id: str | None = None, project: Path = Path(".")):
    """Create a candidate that requires review before ordinary recall."""
    invoke(lambda: store_at(project).propose(content, memory_type=type, source=source,
                                             scope_type=scope, scope_id=scope_id))


@app.command("review")
def review(id: str, accept: bool = typer.Option(..., "--accept/--reject"),
           note: str = typer.Option(..., "--note"), project: Path = Path(".")):
    """Accept or reject a capture candidate with a recorded review note."""
    invoke(lambda: store_at(project).review_candidate(id, accept, note, actor="cli-user"))


@app.command("claim-state")
def claim_state(id: str, state: str,
                note: str = typer.Option(..., "--note"), project: Path = Path(".")):
    """Explicitly update proposal/evaluation/adoption status with an audit note."""
    invoke(lambda: store_at(project).set_claim_state(id, state, note, actor="cli-user"))


@app.command("observe")
def observe(commit: str = "HEAD", project: Path = Path(".")):
    """Explicitly inspect committed changes; no Git hook is installed."""
    invoke(lambda: store_at(project).observe_commit(commit))


@app.command("verify")
def verify(id: str, note: str = typer.Option(..., "--note"), commit: str = "HEAD",
           claim_confidence: float | None = typer.Option(None, "--claim-confidence", min=0.0, max=1.0),
           valid_from: datetime | None = typer.Option(None, "--valid-from"),
           valid_to: datetime | None = typer.Option(None, "--valid-to"),
           project: Path = Path(".")):
    """Confirm an existing memory after reviewing its supporting code."""
    invoke(lambda: store_at(project).verify(id, commit, note, claim_confidence=claim_confidence,
                                            valid_from=valid_from, valid_to=valid_to))


@app.command("supersede")
def supersede(id: str, content: str, note: str = typer.Option(..., "--note"),
              commit: str = "HEAD", file: list[str] = typer.Option([], "--file"),
              claim_value: str | None = None,
              valid_from: datetime | None = typer.Option(None, "--valid-from"),
              valid_to: datetime | None = typer.Option(None, "--valid-to"),
              claim_confidence: float | None = typer.Option(None, "--claim-confidence", min=0.0, max=1.0),
              project: Path = Path(".")):
    """Replace a decision and retain its original evidence."""
    invoke(lambda: store_at(project).supersede(id, content, commit, note, file or None,
                                               claim_value=claim_value, valid_from=valid_from,
                                               valid_to=valid_to, claim_confidence=claim_confidence))


@app.command("recall")
def recall(query: str, file: list[str] = typer.Option([], "--file"),
           symbol: list[str] = typer.Option([], "--symbol"),
           task_id: str | None = None, task_context: str | None = None,
           user_scope_id: str | None = None,
           history: bool = False, token_budget: int = 1500, project: Path = Path(".")):
    """Retrieve current decisions, with evidence and ranking explanations."""
    invoke(lambda: store_at(project).recall_context(
        query, file_paths=file, symbols=symbol, include_history=history, token_budget=token_budget,
        scope_context={key: value for key, value in {
            "task": task_id, "user": user_scope_id,
        }.items() if value}, task_context=task_context,
    ))


@app.command("inspect")
def inspect(project: Path = Path(".")):
    """List all lifecycle states including stale and superseded decisions."""
    invoke(lambda: [
        m.model_dump(mode="json") for m in store_at(project).list_memories(limit=10000)
    ])


@app.command("activity")
def activity(limit: int = 100, project: Path = Path(".")):
    """Inspect recent lifecycle and privacy-minimizing recall events."""
    invoke(lambda: {"events": store_at(project).activity(limit),
                    "ledger": store_at(project).events.status()})


@app.command("review-queue")
def review_queue(include_sensitive: bool = False, limit: int = 100,
                 project: Path = Path(".")):
    """List candidate captures, changed claims, and expired or overdue memories."""
    invoke(lambda: store_at(project).review_queue(include_sensitive, limit))


@app.command("complete-task")
def complete_task(task_id: str, project: Path = Path(".")):
    """Archive task-scoped memory after work is complete."""
    invoke(lambda: store_at(project).complete_task(task_id, actor="cli-user"))


@app.command("find-conflicts")
def find_conflicts(limit: int = 100, project: Path = Path(".")):
    """Generate possible overlap/conflict candidates for review."""
    invoke(lambda: store_at(project).conflict_candidates(limit))
