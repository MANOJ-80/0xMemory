"""Read Git evidence without executing hooks or changing the repository."""

import shutil
import subprocess
from pathlib import Path


class Repository:
    def __init__(self, project_dir: Path):
        self.path = project_dir.resolve()
        self.executable = shutil.which("git")
        if not self.executable:
            windows_git = Path("C:/Program Files/Git/cmd/git.exe")
            if windows_git.exists():
                self.executable = str(windows_git)
        if not self.executable:
            raise ValueError("Git is required for commit evidence")
        root = Path(self.run("rev-parse", "--show-toplevel").strip()).resolve()
        if root != self.path:
            raise ValueError("Initialize the memory store at the Git repository root")

    def run(self, *args: str) -> str:
        result = subprocess.run(
            [self.executable, "-C", str(self.path), *args],
            capture_output=True, encoding="utf-8", errors="replace", timeout=30,
        )
        if result.returncode:
            raise ValueError(result.stderr.strip() or "Git operation failed")
        return result.stdout

    def resolve(self, ref: str) -> str:
        return self.run("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").strip()

    def validate_evidence(self, commit: str, paths: list[str]) -> str:
        sha = self.resolve(commit)
        for path in paths:
            if self.run("cat-file", "-t", sha + ":" + path).strip() != "blob":
                raise ValueError(f"Evidence is not a file at {sha}: {path}")
        return sha

    def changed_paths(self, target: str, base: str | None = None) -> set[str]:
        if base:
            output = self.run("diff", "--name-only", "--no-renames", "-z", base, target, "--")
        else:
            output = self.run(
                "diff-tree", "--root", "--no-commit-id", "-r", "-m",
                "--name-only", "--no-renames", "-z", target, "--",
            )
        return set(filter(None, output.split("\0")))

    def is_ancestor(self, older: str, newer: str) -> bool:
        return self.run("merge-base", older, newer).strip() == older
