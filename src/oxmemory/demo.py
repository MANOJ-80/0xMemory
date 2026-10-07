"""Run a real Git-to-memory lifecycle demo in an isolated temporary repository."""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from oxmemory.core.models import MemoryType
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore


def run_demo() -> dict:
    executable = shutil.which("git")
    if not executable:
        candidate = Path("C:/Program Files/Git/cmd/git.exe")
        if candidate.exists():
            executable = str(candidate)
    if not executable:
        raise ValueError("Git is required for the demo")
    with tempfile.TemporaryDirectory(prefix="0xmemory-demo-") as temp:
        root = Path(temp)

        def git(*args):
            result = subprocess.run([executable, "-C", str(root), *args],
                                    capture_output=True, text=True, check=True)
            return result.stdout.strip()

        git("init")
        git("config", "user.name", "0xMemory Demo")
        git("config", "user.email", "demo@example.invalid")
        git("config", "core.hooksPath", "")
        git("config", "commit.gpgsign", "false")
        (root / "auth.py").write_text('AUTH_METHOD = "jwt"\n', encoding="utf-8")
        git("add", "auth.py")
        git("commit", "-m", "Use JWT authentication")
        before = git("rev-parse", "HEAD")
        MarkdownManager(root).initialize_brain("Authentication demo")
        store = MemoryStore(root, enable_vectors=False)
        old = store.add("Authentication uses JWT", MemoryType.DECISION,
                        file_paths=["auth.py"], commit_sha=before)
        initial = store.recall_context("Authentication")
        (root / "auth.py").write_text('AUTH_METHOD = "cookie_session"\n', encoding="utf-8")
        git("add", "auth.py")
        git("commit", "-m", "Switch to cookie sessions")
        after = git("rev-parse", "HEAD")
        observed = store.observe_commit(after)
        stale_recall = store.recall_context("Authentication")
        new = store.supersede(old.id, "Authentication uses cookie sessions", after,
                              "Demo reviewer checked AUTH_METHOD in auth.py")
        fresh = MemoryStore(root, enable_vectors=False)
        final = fresh.recall_context("Authentication", file_paths=["auth.py"])
        assert not stale_recall["results"]
        assert [item["memory"]["id"] for item in final["results"]] == [new.id]
        return {
            "scenario": "Synthetic authentication migration using real local Git commits",
            "initial_recall": initial, "commit_observation": observed,
            "stale_recall": stale_recall, "fresh_session_recall": final,
            "preserved_history": fresh.get(old.id).model_dump(mode="json"),
            "passed": True,
            "note": "Explicit scripted review; no automatic inference of authentication semantics",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = json.dumps(run_demo(), indent=2)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
