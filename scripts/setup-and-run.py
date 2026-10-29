#!/usr/bin/env python3
"""Cross-platform entry point for installing 0xMemory and preparing its demo."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_CHECK = (
    "import sys; sys.exit(0 if sys.version_info[:2] in {(3, 11), (3, 12)} else 1)"
)


def candidates() -> list[list[str]]:
    """Find an installed Python 3.11/3.12 on Ubuntu or Windows."""
    venv_python = ROOT / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    result: list[list[str]] = []
    if venv_python.is_file():
        result.append([str(venv_python)])
    if sys.executable:
        result.append([sys.executable])

    if os.name == "nt":
        launcher = shutil.which("py")
        if launcher:
            result.extend([[launcher, "-3.12"], [launcher, "-3.11"]])
        python = shutil.which("python")
        if python:
            result.append([python])
    else:
        for name in ("python3.12", "python3.11", "python3"):
            executable = shutil.which(name)
            if executable:
                result.append([executable])

    # Keep order while removing duplicate commands.
    return [list(item) for item in dict.fromkeys(tuple(item) for item in result)]


def choose_python() -> list[str] | None:
    for command in candidates():
        try:
            check = subprocess.run(
                [*command, "-c", VERSION_CHECK],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except OSError:
            continue
        if check.returncode == 0:
            return command
    return None


def main() -> int:
    python = choose_python()
    if python is None:
        print(
            "Install Python 3.11 or 3.12 and Git, then run this script again.\n"
            "Windows: py scripts/setup-and-run.py --project ..\\memory-demo\n"
            "Ubuntu:  python3 scripts/setup-and-run.py --project ../memory-demo",
            file=sys.stderr,
        )
        return 1

    platform_name = "Windows" if os.name == "nt" else "Ubuntu/Linux"
    print(f"Platform: {platform_name}\nPython launcher: {' '.join(python)}", flush=True)
    runner = ROOT / "scripts" / "demo_setup.py"
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    try:
        completed = subprocess.run(
            [*python, str(runner), *sys.argv[1:]],
            cwd=ROOT,
            env=environment,
            check=False,
        )
    except OSError as exc:
        print(f"Could not start the demo setup: {exc}", file=sys.stderr)
        return 1
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
