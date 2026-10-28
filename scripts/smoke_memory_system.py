"""Offline, disposable-repository smoke check for the architecture memory flows."""

import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from oxmemory.core.models import MemoryStatus, MemoryType
from oxmemory.storage.memory_store import MemoryStore


def git(project: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args], check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    passed = []
    with tempfile.TemporaryDirectory(prefix="0xmemory-architecture-smoke-") as temp:
        project = Path(temp).resolve()
        git(project, "init", "-q")
        git(project, "config", "user.name", "0xMemory Smoke")
        git(project, "config", "user.email", "smoke@example.invalid")
        evidence = project / "storage.py"
        evidence.write_text("def backend():\n    return 'json'\n", encoding="utf-8")
        git(project, "add", "storage.py")
        git(project, "commit", "-qm", "initial storage implementation")
        initial = git(project, "rev-parse", "HEAD")

        store = MemoryStore(project, enable_vectors=False)
        store.markdown.initialize_brain(project.name, "Disposable architecture smoke fixture")

        decision = store.add(
            "The application uses JSON task storage for portability.",
            memory_type=MemoryType.DECISION,
            file_paths=["storage.py"], symbols=["backend"], commit_sha=initial,
        )
        assert decision.evidence_refs, "file and symbol evidence anchors were not captured"
        passed.append("evidence anchors")

        recalled = store.recall_context(
            "Why does the application use JSON task storage?", semantic=False,
            file_paths=["storage.py"], token_budget=4000,
        )
        assert decision.id in {item["memory"]["id"] for item in recalled["results"]}
        passed.append("keyword and file-aware recall")

        evidence.write_text("def backend():\n    return 'sqlite'\n", encoding="utf-8")
        git(project, "add", "storage.py")
        git(project, "commit", "-qm", "change storage backend")
        changed = git(project, "rev-parse", "HEAD")
        observed = store.observe_commit(changed)
        assert any(item["id"] == decision.id for item in observed["affected"])
        assert store.get(decision.id).status == MemoryStatus.REVIEW_REQUIRED
        qualified = store.recall_context(
            "Why does the application use JSON task storage?", semantic=False,
            file_paths=["storage.py"], token_budget=4000,
        )
        result = next(item for item in qualified["results"] if item["memory"]["id"] == decision.id)
        assert result["evidence_validation"]["state"] == "unknown"
        assert "review_required" in result["memory"]["status"]
        passed.append("evolution review signal and qualified recall")

        verified = store.verify(decision.id, changed, "Reviewed storage.py and confirmed the claim.")
        assert verified.status == MemoryStatus.ACTIVE_VERIFIED
        passed.append("explicit evidence verification")

        candidate = store.propose("A candidate workflow memory for review.", memory_type=MemoryType.LEARNING)
        assert candidate.status == MemoryStatus.CANDIDATE
        accepted = store.review_candidate(candidate.id, True, "Confirmed as reusable.")
        assert accepted.status == MemoryStatus.ACTIVE_UNVERIFIED
        passed.append("propose and review candidate")

        task_memory = store.add(
            "Task task-17 is waiting on the API schema review.",
            memory_type=MemoryType.TASK_STATE, scope_type="task", scope_id="task-17",
        )
        correct_scope = store.search_ranked(
            "What is task-17 waiting on?", semantic=False,
            scope_context={"task": "task-17"},
        )
        wrong_scope = store.search_ranked(
            "What is task-17 waiting on?", semantic=False,
            scope_context={"task": "task-18"},
        )
        assert task_memory.id in {item["memory"].id for item in correct_scope}
        assert task_memory.id not in {item["memory"].id for item in wrong_scope}
        passed.append("task-scope isolation")

        slot_memory = store.add(
            "SQLite is the selected task database.", memory_type=MemoryType.DECISION,
            answer_slots={"rationale": "Atomic transactions prevent lost updates."},
        )
        slot_context = store.recall_context("Why did we choose SQLite?", semantic=False, token_budget=4000)
        packed_slot_memory = next(
            item["memory"] for item in slot_context["results"] if item["memory"]["id"] == slot_memory.id
        )
        assert packed_slot_memory["answer_slots"] == {
            "rationale": "Atomic transactions prevent lost updates."
        }
        passed.append("answer-slot retrieval and packing")

        sensitive = store.add(
            "Private deployment account owner is devops-team.",
            sensitivity="sensitive",
        )
        sensitive_query = "Private deployment account devops-team"
        ordinary = store.search_ranked(sensitive_query, semantic=False)
        authorized = store.search_ranked(
            sensitive_query, semantic=False, include_sensitive=True,
        )
        assert sensitive.id not in {item["memory"].id for item in ordinary}
        assert sensitive.id in {item["memory"].id for item in authorized}
        passed.append("sensitive recall policy")

        overdue = store.add(
            "The workflow owner should review this note.",
            review_after=datetime.now() - timedelta(days=1),
        )
        assert overdue.id in {item["id"] for item in store.review_queue()}
        assert sensitive.id not in {item["id"] for item in store.review_queue()}
        passed.append("review queue and sensitive exclusion")

        try:
            store.add("api_key = 'smoke_test_secret'", memory_type=MemoryType.FACT)
        except ValueError:
            passed.append("credential-like content refusal")
        else:
            raise AssertionError("credential-like content was accepted")

        ledger = store.events.status()
        assert ledger["chain_valid"] and ledger["events"] > 0, ledger
        passed.append("hash-chained activity ledger")
        store.close()

    report = {"status": "PASS", "checks": passed, "count": len(passed),
              "network_required": False, "target_repository_modified": False}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
