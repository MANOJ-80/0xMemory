"""Offline regression tests: python -m unittest discover -s tests -p test_lifecycle.py."""

import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from oxmemory.core.models import Memory, MemoryStatus, MemoryType
from oxmemory.storage.markdown import MarkdownManager, parse_memory_entries, serialize_memory_entry
from oxmemory.storage.memory_store import MemoryStore


class MemoryLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.markdown = MarkdownManager(self.root)
        self.markdown.initialize_brain("Lifecycle test")
        self.store = MemoryStore(self.root, enable_vectors=False)

    def git(self, *args):
        import shutil
        executable = shutil.which("git") or "C:/Program Files/Git/cmd/git.exe"
        result = subprocess.run([executable, "-C", str(self.root), *args],
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def init_repo(self):
        self.git("init")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Memory Test")
        self.git("config", "commit.gpgsign", "false")

    def commit(self, content, filename="auth.py"):
        (self.root / filename).write_text(content, encoding="utf-8")
        self.git("add", "--", filename)
        self.git("-c", "core.hooksPath=", "commit", "-m", "Update evidence")
        return self.git("rev-parse", "HEAD")

    def test_full_metadata_roundtrip(self):
        memory = Memory(content="Use cookies — session login", file_paths=["src\\auth.py"],
                        confidence=0.8, salience=0.9, related_to=["mem-first"],
                        session_id="session-1", status=MemoryStatus.STALE,
                        revisions=[{"content": "Use JWT"}], symbols=["login"],
                        valid_from=datetime(2026, 1, 1), valid_to=datetime(2026, 6, 1),
                        claim_confidence=0.72,
                        claim_subject="authentication", claim_predicate="uses",
                        claim_value="cookies", claim_environment="production",
                        claim_state="evaluating")
        parsed = parse_memory_entries(serialize_memory_entry(memory), memory.type)[0]
        self.assertEqual(memory.model_dump(), parsed.model_dump())

    def test_legacy_markdown_remains_readable(self):
        text = "## [2026-01-12 10:30] `auth`\n\nUse JWT\n\n_Source: manual_\n_ID: legacy_\n---\n"
        memory = parse_memory_entries(text, MemoryType.DECISION)[0]
        self.assertEqual(memory.id, "legacy")
        self.assertEqual(memory.status, MemoryStatus.ACTIVE)

    def test_delete_middle_preserves_neighbors(self):
        entries = [self.store.add(f"Decision {i}") for i in range(3)]
        self.assertTrue(self.store.delete(entries[1].id))
        self.assertEqual({m.id for m in self.store.list_memories()}, {entries[0].id, entries[2].id})

    def test_update_retains_history_and_updates_vector(self):
        memory = self.store.add("JWT login")
        vector = Mock()
        self.store._vector_store = vector
        self.store.update(memory.id, "Cookie login")
        updated = self.store.get(memory.id)
        self.assertEqual(updated.revisions[0]["content"], "JWT login")
        vector.upsert.assert_called_once()
        self.assertEqual(vector.upsert.call_args.args[0].content, "Cookie login")
        vector.delete.assert_not_called()
        self.assertEqual(updated.status, MemoryStatus.REVIEW_REQUIRED)

    def test_text_correction_invalidates_structured_claim_annotations(self):
        memory = self.store.add(
            "Production uses PostgreSQL", claim_subject="production database",
            claim_predicate="uses", claim_value="PostgreSQL",
            answer_slots={"approval": "approved"},
        )
        corrected = self.store.update(memory.id, "Production is evaluating MySQL")
        self.assertEqual(corrected.revisions[0]["claim_value"], "PostgreSQL")
        self.assertIsNone(corrected.claim_subject)
        self.assertIsNone(corrected.claim_value)
        self.assertEqual(corrected.answer_slots, {})
        self.assertEqual(corrected.status, MemoryStatus.REVIEW_REQUIRED)

    def test_duplicate_ingestion_is_idempotent(self):
        first = self.store.add("Use cookie sessions")
        second = self.store.add("Use  cookie sessions")
        self.assertEqual(first.id, second.id)
        self.assertEqual(len(self.store.list_memories()), 1)

    def test_commit_to_fresh_session_retrieval(self):
        self.init_repo()
        first = self.commit('AUTH = "jwt"\n')
        old = self.store.add("Authentication uses JWT", MemoryType.DECISION,
                             file_paths=["auth.py"], commit_sha=first)
        second = self.commit('AUTH = "cookie"\n')
        result = self.store.observe_commit(second)
        self.assertEqual(result["affected"][0]["id"], old.id)
        self.assertEqual(self.store.get(old.id).status, MemoryStatus.REVIEW_REQUIRED)
        recalled = self.store.search_ranked("Authentication", semantic=False)
        self.assertIn(old.id, {item["memory"].id for item in recalled})
        self.assertEqual(recalled[0]["evidence_validation"]["state"], "unknown")
        self.assertEqual(self.store.observe_commit(second)["affected"], [])
        new = self.store.supersede(old.id, "Authentication uses cookie sessions", second,
                                   "Reviewed AUTH in auth.py")
        fresh = MemoryStore(self.root, enable_vectors=False)
        self.assertEqual([m.id for m in fresh.search("Authentication")], [new.id])
        self.assertEqual(fresh.get(old.id).superseded_by, new.id)
        self.assertEqual(fresh.get(new.id).supersedes, old.id)
        self.assertEqual(len(fresh.search("Authentication", include_history=True)), 2)
        self.assertNotIn("JWT", fresh.get_decisions_context())
        self.assertEqual(fresh.observe_commit(first)["affected"], [])

    def test_unrelated_change_does_not_invalidate(self):
        self.init_repo()
        first = self.commit("AUTH = 'jwt'")
        memory = self.store.add("Use JWT", file_paths=["auth.py"], commit_sha=first)
        second = self.commit("COLOR = 'blue'", "ui.py")
        self.assertEqual(self.store.observe_commit(second)["affected"], [])
        self.assertEqual(self.store.get(memory.id).status, MemoryStatus.ACTIVE)

    def test_deleted_linked_evidence_is_distinguished_from_uncertain_edit(self):
        self.init_repo()
        first = self.commit("AUTH = 'jwt'")
        memory = self.store.add("Authentication uses JWT", file_paths=["auth.py"], commit_sha=first)
        (self.root / "auth.py").unlink()
        self.git("add", "-u", "--", "auth.py")
        self.git("-c", "core.hooksPath=", "commit", "-m", "Remove legacy auth")
        repository = __import__("oxmemory.storage.repository", fromlist=["Repository"]).Repository(self.root)
        assessment = repository.assess_evidence(
            memory.commit_sha, memory.evidence_branch, memory.file_paths,
            repository.current_context(), memory.evidence_refs,
        )
        self.assertEqual(assessment["state"], "evidence_missing")

    def test_claim_validity_end_is_exclusive(self):
        from datetime import date
        from oxmemory.storage.query_planner import claim_valid_at

        memory = Memory(content="Database uses PostgreSQL",
                        valid_from=datetime(2026, 1, 1), valid_to=datetime(2026, 2, 1))
        self.assertTrue(claim_valid_at(memory, date(2026, 1, 31)))
        self.assertFalse(claim_valid_at(memory, date(2026, 2, 1)))

    def test_evaluated_claim_is_not_current_adoption_and_is_available_for_approval_query(self):
        from oxmemory.core.config import get_default_config, save_config

        save_config(get_default_config("Claim state"), self.root)
        evaluated = self.store.add(
            "CockroachDB is under evaluation for production",
            claim_subject="production database", claim_predicate="uses",
            claim_value="CockroachDB", claim_environment="production",
            claim_state="evaluating",
        )
        current = self.store.search_ranked("Which database is currently used in production?")
        self.assertNotIn(evaluated.id, {row["memory"].id for row in current})
        approval = self.store.search_ranked("Did we approve CockroachDB for production?")
        self.assertIn(evaluated.id, {row["memory"].id for row in approval})
        self.assertEqual(approval[0]["memory"].claim_state, "evaluating")

    def test_explicit_historical_query_retrieves_labeled_session_evidence(self):
        from oxmemory.core.config import get_default_config, save_config
        from oxmemory.core.models import Message

        save_config(get_default_config("Session history"), self.root)
        session = self.store.sessions.create_session("Database evaluation")
        self.store.sessions.add_message(
            session.id, Message(role="assistant", content="We tried SQLite for the local prototype.")
        )
        result = self.store.recall_context("What happened when we previously tried SQLite?")
        self.assertEqual(result["status"], "historical_evidence_available")
        self.assertEqual(result["historical_evidence"][0]["session_id"], session.id)
        self.assertIn("Historical conversation evidence", result["context"])

    def test_claim_state_changes_are_explicit_and_audited(self):
        memory = self.store.add("PostgreSQL is proposed for production", claim_state="proposed")
        with self.assertRaises(ValueError):
            self.store.set_claim_state(memory.id, "adopted", "")
        updated = self.store.set_claim_state(memory.id, "adopted", "Approved in the design review")
        self.assertEqual(updated.claim_state, "adopted")
        self.assertEqual(updated.revisions[-1]["claim_state"], "proposed")
        self.assertEqual(self.store.activity(1)[0]["action"], "claim_state_changed")

    def test_review_cannot_use_evidence_before_known_change(self):
        self.init_repo()
        first = self.commit("AUTH = 'jwt'")
        memory = self.store.add("Use JWT", file_paths=["auth.py"], commit_sha=first)
        second = self.commit("AUTH = 'cookie'")
        self.store.observe_commit(second)
        with self.assertRaises(ValueError):
            self.store.verify(memory.id, first, "Outdated evidence")
        with self.assertRaises(ValueError):
            self.store.supersede(memory.id, "Use cookies", first, "Outdated evidence")
        self.assertEqual(self.store.get(memory.id).status, MemoryStatus.REVIEW_REQUIRED)
        third = self.commit("AUTH = 'sso'")
        self.store.observe_commit(third)
        self.assertEqual(self.store.get(memory.id).stale_at_commit, third)
        with self.assertRaises(ValueError):
            self.store.verify(memory.id, second, "Still outdated")

    def test_verify_retains_valid_fact_after_file_edit(self):
        self.init_repo()
        first = self.commit("AUTH = 'jwt'")
        memory = self.store.add("Use JWT", file_paths=["auth.py"], commit_sha=first)
        second = self.commit("# Refactor comment\nAUTH = 'jwt'")
        self.store.observe_commit(second)
        verified = self.store.verify(memory.id, second, "AUTH still uses JWT")
        self.assertEqual(verified.status, MemoryStatus.ACTIVE_VERIFIED)
        self.assertEqual(verified.commit_sha, second)
        self.assertEqual(self.store.observe_commit(second)["affected"], [])

    def test_structured_claim_supersession_closes_old_validity(self):
        self.init_repo()
        first = self.commit('ENGINE = "sqlite"', "db.py")
        old = self.store.add(
            "Production database uses SQLite", file_paths=["db.py"], commit_sha=first,
            claim_subject="production database", claim_predicate="uses",
            claim_value="SQLite", claim_environment="production",
        )
        second = self.commit('ENGINE = "postgresql"', "db.py")
        replacement = self.store.supersede(
            old.id, "Production database uses PostgreSQL", second,
            "Reviewed the migration", claim_value="PostgreSQL",
        )
        self.assertEqual(replacement.claim_value, "PostgreSQL")
        self.assertIsNotNone(replacement.valid_from)
        self.assertEqual(self.store.get(old.id).valid_to, replacement.valid_from)

    def test_bad_evidence_does_not_change_history(self):
        self.init_repo()
        first = self.commit("AUTH = 'jwt'")
        memory = self.store.add("Use JWT", file_paths=["auth.py"], commit_sha=first)
        with self.assertRaises(ValueError):
            self.store.supersede(memory.id, "Use cookies", first, "Checked", ["missing.py"])
        self.assertEqual(self.store.get(memory.id).status, MemoryStatus.ACTIVE)
        self.assertEqual(len(self.store.list_memories()), 1)
        for path in ["../secret", "C:\\secret", "/etc/passwd"]:
            with self.assertRaises(ValueError):
                Memory(content="Test", file_paths=[path])

    def test_file_relevance_and_bounded_context(self):
        self.store.add("Login is handled by middleware")
        linked = self.store.add("Cookie expiry is one hour", file_paths=["auth.py"])
        results = self.store.search_ranked("Login", semantic=False, file_paths=["auth.py"],
                                           relevance_gate=False)
        self.assertEqual(results[0]["memory"].id, linked.id)
        self.assertIn("linked file match", results[0]["reasons"])
        context = self.store.recall_context("Login", file_paths=["auth.py"], token_budget=300)
        self.assertLessEqual(context["budget_used"], 300)
        self.assertEqual(self.store.recall_context("Login", token_budget=1)["context"], "")

    def test_vector_and_keyword_results_are_fused_and_filtered(self):
        first = self.store.add("Login cookies")
        second = self.store.add("Session expiry")
        stale = self.store.add("Old login")
        stale.status = MemoryStatus.STALE
        self.store._persist(stale)
        vector = Mock()
        vector.search.return_value = [{"id": stale.id, "similarity": 0.9},
                                      {"id": second.id, "similarity": 0.8}]
        self.store._vector_store = vector
        results = self.store.search_ranked("Login")
        ids = {r["memory"].id for r in results}
        self.assertEqual(ids, {first.id, second.id})

    def test_sync_repairs_edited_and_removed_entries(self):
        memory = self.store.add("Current decision")
        vector = Mock()
        vector.get_all_ids.return_value = [memory.id, "deleted"]
        self.store._vector_store = vector
        result = self.store.sync_vectors()
        vector.upsert.assert_called_once()
        vector.delete.assert_called_once_with("deleted")
        self.assertEqual(result["removed"], 1)

    def test_context_manager_closes_even_after_failure_without_loading_backend(self):
        vector = Mock()
        with self.assertRaises(RuntimeError):
            with self.store as store:
                store._vector_store = vector
                raise RuntimeError("Test failure")
        vector.close.assert_called_once()
        self.store.close()
        vector.close.assert_called_once()

    def test_vector_close_releases_client_and_cached_collection(self):
        from oxmemory.storage.vector_store import VectorStore
        vector = VectorStore(self.root)
        client = Mock()
        vector._client = client
        vector._collection = Mock()
        vector.close()
        vector.close()
        client.close.assert_called_once()
        self.assertIsNone(vector._client)
        self.assertIsNone(vector._collection)


if __name__ == "__main__":
    unittest.main()
