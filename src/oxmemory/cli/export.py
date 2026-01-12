"""Export command implementation."""

import csv
import json
import logging
from pathlib import Path

import typer
from rich.console import Console

from oxmemory.core.models import Memory, MemoryType
from oxmemory.storage.memory_store import MemoryStore

logger = logging.getLogger(__name__)
console = Console()
app = typer.Typer()


@app.callback(invoke_without_command=True)
def export(
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output file path (ends in .json or .csv)",
    ),
    type: MemoryType | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by memory type (fact, decision, etc.)",
    ),
    project_dir: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Project directory (defaults to current)",
    ),
) -> None:
    """Export memories to JSON or CSV.

    Examples:
        0xmemory export -o backup.json
        0xmemory export -o decisions.csv --type decision
    """
    try:
        store = MemoryStore(project_dir, enable_vectors=False)
    except Exception as e:
        console.print(f"[red]Error loading brain:[/red] {e}")
        raise typer.Exit(1)

    # Get memories
    if type:
        memories = store.markdown.read_memories(type)
    else:
        memories = store.markdown.get_all_memories()

    if not memories:
        console.print("[yellow]No memories found to export.[/yellow]")
        return

    # Export based on file extension
    ext = output.suffix.lower()

    if ext == ".json":
        _export_json(memories, output)
    elif ext == ".csv":
        _export_csv(memories, output)
    else:
        console.print(f"[red]Unsupported format: {ext}[/red]")
        console.print("Please use .json or .csv")
        raise typer.Exit(1)

    console.print(f"[green]✅ Exported {len(memories)} memories to {output}[/green]")


def _export_json(memories: list[Memory], output: Path) -> None:
    """Export list of memories to JSON file."""
    data = [m.model_dump(mode="json") for m in memories]
    output.write_text(json.dumps(data, indent=2))


def _export_csv(memories: list[Memory], output: Path) -> None:
    """Export list of memories to CSV file."""
    if not memories:
        return

    # Get fields from first memory
    fields = list(memories[0].model_dump().keys())

    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for m in memories:
            row = m.model_dump(mode="json")
            # Flatten lists/dicts for CSV
            for k, v in row.items():
                if isinstance(v, (list, dict)):
                    row[k] = json.dumps(v)
            writer.writerow(row)
