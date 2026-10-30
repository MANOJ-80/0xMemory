#!/usr/bin/env python3
"""Run one Codex CLI coding-agent trial and capture turn-reported token usage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--usage-file", type=Path, required=True)
    parser.add_argument("--model", required=True, help="Pinned Codex model identifier")
    args = parser.parse_args()

    repo = args.repo.resolve()
    prompt = args.prompt_file.resolve().read_text(encoding="utf-8")
    usage_path = args.usage_file.resolve()
    codex = shutil.which("codex")
    if not codex:
        parser.error("Codex CLI was not found on PATH")

    command = [
        codex,
        "--model", args.model,
        "--sandbox", "workspace-write",
        "--ask-for-approval", "never",
        "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-",
    ]
    turns: list[dict] = []
    completed_turns = 0
    process = subprocess.Popen(
        command,
        cwd=repo,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(prompt)
    process.stdin.close()

    # Forward the JSONL stream unchanged so the invoking harness preserves its
    # audit log. Extract only documented usage payloads into the usage artifact.
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "turn.completed":
            continue
        completed_turns += 1
        usage = event.get("usage")
        if isinstance(usage, dict):
            turns.append({
                "turn_index": completed_turns,
                "usage": {key: usage[key] for key in USAGE_FIELDS if key in usage},
            })
    returncode = process.wait()

    totals = {}
    for key in USAGE_FIELDS:
        values = [turn["usage"][key] for turn in turns if key in turn["usage"]]
        totals[key] = sum(values) if values else None
    report = {
        "source": "codex_cli_turn_completed_usage",
        "granularity": "agent_turn",
        "model_requested": args.model,
        "codex_version": _version(codex),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "returncode": returncode,
        "turns_completed": completed_turns,
        "turns_with_usage": len(turns),
        "usage_coverage": len(turns) / completed_turns if completed_turns else None,
        "totals": totals,
        "turn_usage": turns,
        "limitations": [
            "Counts are Codex-reported turn totals, not per-HTTP-request billing records.",
            "A null field was not exposed; null does not mean zero.",
            "Monetary cost is not inferred from token counts.",
        ],
    }
    usage_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return returncode


def _version(codex: str) -> str | None:
    try:
        result = subprocess.run([codex, "--version"], capture_output=True, text=True,
                                encoding="utf-8", timeout=10, check=False)
        return result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
