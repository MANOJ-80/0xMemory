"""Explicit, auditable memory lifecycle operations.

File changes invalidate confidence in evidence; they do not infer a new fact.
Verification and replacement record the caller's assessment, not a proof of truth.
"""

import logging
from datetime import datetime

from oxmemory.core.models import Memory, MemoryStatus
from oxmemory.storage.repository import Repository

logger = logging.getLogger(__name__)


class LifecycleMixin:
    def _index(self, memory: Memory) -> None:
        try:
            if self.vector_store:
                self.vector_store.upsert(memory)
        except Exception as exc:
            logger.warning("Vector index needs repair: %s", exc)

    def _persist(self, memory: Memory) -> None:
        if not self.markdown.replace_entries(memory.type, {memory.id: memory}):
            raise ValueError(f"Memory disappeared: {memory.id}")
        self._index(memory)

    def _require(self, memory_id: str) -> Memory:
        memory = self.get(memory_id)
        if memory is None:
            raise ValueError(f"Memory not found: {memory_id}")
        return memory

    def _review_commit(self, memory: Memory, commit: str, paths: list[str]) -> str:
        repo = Repository(self.project_dir)
        sha = repo.validate_evidence(commit, paths)
        baseline = memory.stale_at_commit or memory.commit_sha
        if baseline and not repo.is_ancestor(repo.resolve(baseline), sha):
            raise ValueError("Review commit must include the latest known evidence change")
        return sha

    def observe_commit(self, commit: str = "HEAD") -> dict:
        repo = Repository(self.project_dir)
        target = repo.resolve(commit)
        changed = repo.changed_paths(target)
        affected = []
        for memory in self.markdown.get_all_memories():
            if memory.status == MemoryStatus.SUPERSEDED or not memory.file_paths:
                continue
            paths = changed
            baseline = memory.stale_at_commit or memory.commit_sha
            if baseline:
                base = repo.resolve(baseline)
                if repo.is_ancestor(target, base):
                    continue  # Replaying an older commit cannot invalidate newer evidence.
                paths = repo.changed_paths(target, base)
            overlap = sorted(set(memory.file_paths) & paths)
            if not overlap:
                continue
            memory.revisions.append(memory.model_dump(mode="json", exclude={"revisions"}))
            memory.status = MemoryStatus.STALE
            memory.stale_at_commit = target
            memory.verification_note = "Supporting files changed; verification required."
            memory.updated_at = datetime.now()
            self._persist(memory)
            affected.append({"id": memory.id, "files": overlap})
        return {"commit": target, "changed_files": sorted(changed), "affected": affected}

    def verify(self, memory_id: str, commit: str, note: str) -> Memory:
        memory = self._require(memory_id)
        if memory.status == MemoryStatus.SUPERSEDED:
            raise ValueError("Superseded memories cannot be reactivated; create a new decision")
        if not note.strip() or not memory.file_paths:
            raise ValueError("Verification requires a note and linked evidence files")
        sha = self._review_commit(memory, commit, memory.file_paths)
        memory.revisions.append(memory.model_dump(mode="json", exclude={"revisions"}))
        memory.status = MemoryStatus.ACTIVE
        memory.commit_sha = sha
        memory.stale_at_commit = None
        memory.verification_note = note.strip()
        memory.updated_at = datetime.now()
        self._persist(memory)
        return memory

    def supersede(self, memory_id: str, content: str, commit: str, note: str,
                  file_paths: list[str] | None = None) -> Memory:
        old = self._require(memory_id)
        if old.status == MemoryStatus.SUPERSEDED:
            raise ValueError("Memory already superseded")
        if not note.strip():
            raise ValueError("A verification note is required")
        replacement = Memory(
            content=content, type=old.type, tags=old.tags, source="verified-replacement",
            file_paths=old.file_paths if file_paths is None else file_paths,
            symbols=old.symbols, salience=old.salience, supersedes=old.id,
            related_to=[old.id], verification_note=note.strip(),
        )
        if not replacement.file_paths:
            raise ValueError("Replacement requires linked evidence files")
        replacement.commit_sha = self._review_commit(old, commit, replacement.file_paths)
        old.revisions.append(old.model_dump(mode="json", exclude={"revisions"}))
        old.status = MemoryStatus.SUPERSEDED
        old.superseded_by = replacement.id
        old.updated_at = datetime.now()
        # Both records share a type/file. One atomic replacement avoids half a lifecycle transition.
        self.markdown.replace_with_successor(old, replacement)
        self._index(old)
        self._index(replacement)
        return replacement
