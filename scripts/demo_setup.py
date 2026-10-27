"""Shared Windows/Ubuntu demo setup. Invoked by setup-demo.ps1 or setup-demo.sh."""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fresh_project(value):
    project = Path(value).expanduser().resolve()
    if project.exists():
        raise ValueError(
            f"Project already exists: {project}. Choose a new --project; nothing was reset."
        )
    if project.is_relative_to(ROOT) or ROOT.is_relative_to(project):
        raise ValueError("The demo must be outside the engine repository, not its parent.")
    if not project.parent.is_dir():
        raise ValueError(f"Create the parent directory first: {project.parent}")
    return project


class Runner:
    def __init__(self, directory, env):
        self.directory, self.env = directory, env
        self.steps = []

    def run(self, label, command, cwd=ROOT, show_output=True):
        print(f"\n== {label} ==", flush=True)
        with (self.directory / "setup.log").open("a", encoding="utf-8") as log:
            log.write(f"\n== {label} ==\n")
            log.flush()
            process = subprocess.Popen(
                [str(x) for x in command],
                cwd=cwd,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in process.stdout:
                if show_output:
                    print(line, end="", flush=True)
                log.write(line)
            process.stdout.close()
            code = process.wait()
        self.steps.append(dict(step=label, exit_code=code))
        if code:
            raise RuntimeError(f"{label} failed (exit {code}). Read {self.directory / 'setup.log'}")


def handoff(project, python, directory):
    def ps(value):
        return "'" + str(value).replace("'", "''") + "'"

    test = (
        f"& {ps(python)} -m unittest -v"
        if os.name == "nt"
        else f"{shlex.quote(str(python))} -m unittest -v"
    )
    text = (ROOT / "DEMO_FLOW.md").read_text(encoding="utf-8")
    text = text.replace("{{PROJECT}}", project.name).replace("{{TEST_COMMAND}}", test)
    (directory / "DEMO_FLOW.md").write_text(text, encoding="utf-8")
    shutil.copyfile(ROOT / "TEST_REPORT_TEMPLATE.md", directory / "TEST_REPORT.md")
    if os.name == "nt":
        launch = (
            f"Set-Location -LiteralPath {ps(project)}\n& {ps(python)} "
            "-m uvicorn app:app --host 127.0.0.1 --port 8090\nexit $LASTEXITCODE\n"
        )
        filename = "run-app.ps1"
    else:
        launch = (
            f"#!/usr/bin/env bash\nset -euo pipefail\ncd -- {shlex.quote(str(project))}\n"
            f"exec {shlex.quote(str(python))} "
            "-m uvicorn app:app --host 127.0.0.1 --port 8090\n"
        )
        filename = "run-app.sh"
    (directory / filename).write_text(launch, encoding="utf-8", newline="\n")
    print(f"\nApp folder: {project}\nPrompts and evidence: {directory}")
    print(f"Run the app: {directory / filename}\nBrowser: http://127.0.0.1:8090")
    print("Open the APP folder in VS Code/Codex. Sign in and trust the project manually.")
    print("Use one MCP client at a time. Follow DEMO_FLOW.md in the evidence folder.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT.parent / "testTodoapp")
    parser.add_argument(
        "--clients",
        nargs="+",
        choices=["vscode", "codex", "cursor", "antigravity"],
        default=["vscode", "codex"],
    )
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--offline-models", action="store_true")
    parser.add_argument("--full-verify", action="store_true")
    parser.add_argument("--mcp-transport", choices=["native", "anonymous"], default="native")
    args = parser.parse_args()
    try:
        project = fresh_project(args.project)
        git = shutil.which("git")
        if not git and os.name == "nt":
            candidate = Path("C:/Program Files/Git/cmd/git.exe")
            git = str(candidate) if candidate.is_file() else None
        if not git:
            raise ValueError("Install Git, then rerun setup.")
        python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.is_file() and (ROOT / ".venv").exists():
            raise ValueError("Existing .venv is not usable on this OS. Use a fresh engine clone.")
        if args.skip_install and not python.is_file():
            raise ValueError("--skip-install requires an installed engine .venv")
        if sys.version_info[:2] not in [(3, 11), (3, 12)]:
            raise ValueError("Run setup with Python 3.11 or 3.12")
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    # A unique sibling keeps prompts/logs out of the agent app and engine Git trees.
    directory = Path(tempfile.mkdtemp(prefix=project.name + "-evidence-", dir=project.parent))
    env = dict(
        os.environ,
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
        HF_HUB_OFFLINE="1" if args.offline_models else "0",
        TRANSFORMERS_OFFLINE="1" if args.offline_models else "0",
    )
    env["PATH"] = str(Path(git).parent) + os.pathsep + env.get("PATH", "")
    runner = Runner(directory, env)
    report = dict(
        project=str(project),
        python=str(python),
        clients=args.clients,
        status="running",
        full_verification="NOT RUN",
        mcp_transport=args.mcp_transport,
    )
    try:
        if not python.is_file():
            runner.run(
                "Create engine virtual environment", [sys.executable, "-m", "venv", ROOT / ".venv"]
            )
        runner.run(
            "Check interpreter",
            [
                python,
                "-c",
                "import sys; assert sys.version_info[:2] in [(3,11),(3,12)], "
                '"Use Python 3.11/3.12"',
            ],
        )
        if not args.skip_install:
            runner.run(
                "Install engine and test dependencies",
                [python, "-m", "pip", "install", "-e", ".[dev]"],
            )
        runner.run("Check dependencies", [python, "-m", "pip", "check"])
        runner.run("Record installed packages", [python, "-m", "pip", "freeze"], show_output=False)
        runner.run(
            "Check/download embeddings",
            [
                python,
                "-c",
                "from sentence_transformers import SentenceTransformer; "
                "a=SentenceTransformer('all-MiniLM-L6-v2').encode(['setup check']); "
                "assert a.shape==(1,384); print('PASS: embedding shape', a.shape)",
            ],
        )
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        if args.full_verify:
            runner.run(
                "Full engine suite",
                [python, "-m", "pytest", "tests/", "-v", "--basetemp", directory / "pytest"],
            )
            runner.run(
                "Git memory demo",
                [python, "-m", "oxmemory.demo", "--output", directory / "demo.json"],
            )
            runner.run(
                "Semantic evaluation",
                [
                    python,
                    "-m",
                    "oxmemory.evaluation",
                    "--semantic",
                    "--output",
                    directory / "evaluation.json",
                ],
            )
            report["full_verification"] = "PASS"
        print(f"\nCreating fresh To-do project: {project}", flush=True)
        shutil.copytree(
            ROOT / "examples/todo-starter",
            project,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
        )
        runner.run("Initialize app Git repository", [git, "init"], cwd=project)
        runner.run(
            "Stage starter",
            [
                git,
                "add",
                "app.py",
                "storage.py",
                "index.html",
                "test_app.py",
                "README.md",
                "requirements.txt",
                ".gitignore",
                ".github/copilot-instructions.md",
                "AGENTS.md",
            ],
            cwd=project,
        )
        runner.run(
            "Commit starter (local demo identity)",
            [
                git,
                "-c",
                "user.name=Todo Demo",
                "-c",
                "user.email=demo@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                "Create JSON-backed To-do app",
            ],
            cwd=project,
        )
        runner.run("Record initial commit", [git, "rev-parse", "HEAD"], cwd=project)
        runner.run(
            "Initialize app brain",
            [python, "-m", "oxmemory", "init", "--name", project.name, "--local"],
            cwd=project,
        )
        runner.run("Starter app tests", [python, "-m", "unittest", "-v"], cwd=project)
        runner.run(
            "Configure selected clients",
            [
                python,
                ROOT / "scripts/configure-editors.py",
                "--project",
                project,
                "--offline-models",
                "--clients",
                *args.clients,
            ],
        )
        runner.run(
            "Real MCP read-only smoke check",
            [
                python,
                ROOT / "scripts/check-demo-mcp.py",
                "--project",
                project,
                "--output",
                directory / "mcp-smoke.json",
                "--transport",
                args.mcp_transport,
            ],
        )
        handoff(project, python, directory)
        report["status"] = "PASS"
        print("\nPASS: demo preparation. Interactive client/lifecycle checks remain NOT RUN.")
    except (OSError, RuntimeError, ValueError) as exc:
        report.update(status="FAIL", error=str(exc))
        print(
            f"\nFAILED: {exc}\nEvidence: {directory}\n"
            "Existing files were preserved; use a new project path for a fresh retry.",
            file=sys.stderr,
        )
    finally:
        report["steps"] = runner.steps
        (directory / "setup-result.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
