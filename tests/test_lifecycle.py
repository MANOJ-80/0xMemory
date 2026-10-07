"""Offline regression tests: python -m unittest discover -s tests -p test_lifecycle.py."""

import subprocess
import tempfile
import unittest
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
                        revisions=[{"content": "Use JWT"}], symbols=["login"])
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
        self.assertEqual(self.store.search("Authentication", semantic=False), [])
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
        self.assertEqual(self.store.get(memory.id).status, MemoryStatus.STALE)
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
        self.assertEqual(verified.status, MemoryStatus.ACTIVE)
        self.assertEqual(verified.commit_sha, second)
        self.assertEqual(self.store.observe_commit(second)["affected"], [])

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
        results = self.store.search_ranked("Login", semantic=False, file_paths=["auth.py"])
        self.assertEqual(results[0]["memory"].id, linked.id)
        self.assertIn("linked file match", results[0]["reasons"])
        context = self.store.recall_context("Login", file_paths=["auth.py"], token_budget=300)
        self.assertLessEqual(len(context["context"].encode("utf-8")), 300)
        self.assertEqual(self.store.recall_context("Login", token_budget=1)["context"], "")

    def test_vector_and_keyword_results_are_fused_and_filtered(self):
        first = self.store.add("Login cookies")
        second = self.store.add("Session expiry")
        stale = self.store.add("Old login")
        stale.status = MemoryStatus.STALE
        self.store._persist(stale)
        vector = Mock()
        vector.search.return_value = [{"id": stale.id}, {"id": second.id}]
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
