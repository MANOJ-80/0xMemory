"""Explicit, auditable memory lifecycle operations.

File changes trigger review; they do not infer that a claim is false.
Verification and replacement record the caller's assessment, not a proof of truth.
"""

import logging
import hashlib
from datetime import datetime

from oxmemory.core.models import Memory, MemoryStatus
from oxmemory.storage.repository import Repository

logger = logging.getLogger(__name__)


class LifecycleMixin:
    def _index(self, memory: Memory) -> None:
        try:
            if self.vector_store:
                if memory.sensitivity != "normal":
                    self.vector_store.delete(memory.id)
                    return
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

    def set_claim_state(self, memory_id: str, state: str, note: str,
                        actor: str = "local-user") -> Memory:
        """Record an explicit proposal/evaluation/adoption decision without inferring it."""
        allowed = {"asserted", "proposed", "evaluating", "adopted", "rejected", "unknown"}
        if state not in allowed:
            raise ValueError(f"claim state must be one of: {', '.join(sorted(allowed))}")
        if not note.strip():
            raise ValueError("A note is required to change claim state")
        memory = self._require(memory_id)
        if memory.status in {MemoryStatus.CANDIDATE, MemoryStatus.QUARANTINED,
                             MemoryStatus.SUPERSEDED, MemoryStatus.ARCHIVED}:
            raise ValueError("Claim state can only be changed on a reviewable, non-archived memory")
        if memory.claim_state == state:
            return memory
        memory.revisions.append(memory.model_dump(mode="json", exclude={"revisions"}))
        memory.claim_state = state
        memory.provenance = {
            **memory.provenance,
            "claim_state_review": {"actor": actor, "state": state,
                                   "note": note.strip(), "at": datetime.now().isoformat()},
        }
        memory.updated_at = datetime.now()
        self._persist(memory)
        self.events.append(memory.id, "claim_state_changed", actor=actor,
                           reason="claim-state-note-sha256:" + hashlib.sha256(note.strip().encode()).hexdigest(),
                           memory_type=memory.type.value, status=memory.status.value,
                           revision=len(memory.revisions))
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
            if memory.status in {MemoryStatus.SUPERSEDED, MemoryStatus.CANDIDATE,
                                 MemoryStatus.QUARANTINED, MemoryStatus.ARCHIVED} or not memory.file_paths:
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
            if memory.status == MemoryStatus.REVIEW_REQUIRED and memory.stale_at_commit == target:
                continue  # Repeated observation is idempotent.
            memory.revisions.append(memory.model_dump(mode="json", exclude={"revisions"}))
            # A changed supporting file is a review signal, not proof that the
            # natural-language claim is false. Keep it eligible for qualified recall.
            memory.status = MemoryStatus.REVIEW_REQUIRED
            memory.stale_at_commit = target
            memory.verification_note = "Supporting files changed; verification required."
            memory.updated_at = datetime.now()
            self._persist(memory)
            self.events.append(memory.id, "evidence_changed", reason="linked files changed",
                               memory_type=memory.type.value, status=memory.status.value,
                               revision=len(memory.revisions))
            affected.append({"id": memory.id, "files": overlap})
        return {"commit": target, "changed_files": sorted(changed), "affected": affected}

    def verify(self, memory_id: str, commit: str, note: str, *,
               claim_confidence: float | None = None,
               valid_from: datetime | None = None,
               valid_to: datetime | None = None) -> Memory:
        memory = self._require(memory_id)
        if memory.status in {MemoryStatus.CANDIDATE, MemoryStatus.QUARANTINED}:
            raise ValueError("Capture candidates must be accepted/reviewed before evidence verification")
        if memory.status == MemoryStatus.SUPERSEDED:
            raise ValueError("Superseded memories cannot be reactivated; create a new decision")
        if not note.strip() or not memory.file_paths:
            raise ValueError("Verification requires a note and linked evidence files")
        sha = self._review_commit(memory, commit, memory.file_paths)
        repo = Repository(self.project_dir)
        memory.revisions.append(memory.model_dump(mode="json", exclude={"revisions"}))
        memory.status = MemoryStatus.ACTIVE_VERIFIED
        memory.commit_sha = sha
        memory.evidence_branch = repo.current_context()["branch"]
        memory.evidence_refs = repo.capture_evidence(sha, memory.file_paths, memory.symbols)
        memory.stale_at_commit = None
        memory.verification_note = note.strip()
        if claim_confidence is not None:
            memory.claim_confidence = claim_confidence
        if valid_from is not None:
            memory.valid_from = (datetime.fromisoformat(valid_from.replace("Z", "+00:00"))
                                 if isinstance(valid_from, str) else valid_from)
        if valid_to is not None:
            memory.valid_to = (datetime.fromisoformat(valid_to.replace("Z", "+00:00"))
                               if isinstance(valid_to, str) else valid_to)
        # Re-validate half-open claim interval and its structured metadata.
        memory = Memory.model_validate(memory.model_dump())
        memory.updated_at = datetime.now()
        self._persist(memory)
        self.events.append(memory.id, "verified", reason="review-note-sha256:" + hashlib.sha256(note.strip().encode()).hexdigest(),
                           memory_type=memory.type.value, status=memory.status.value,
                           revision=len(memory.revisions))
        return memory

    def supersede(self, memory_id: str, content: str, commit: str, note: str,
                  file_paths: list[str] | None = None, *, claim_value: str | None = None,
                  valid_from: datetime | None = None, valid_to: datetime | None = None,
                  claim_confidence: float | None = None) -> Memory:
        from oxmemory.storage.security import contains_obvious_secret

        if contains_obvious_secret(content):
            raise ValueError("Credential-like content cannot be saved as memory")
        old = self._require(memory_id)
        if old.status in {MemoryStatus.CANDIDATE, MemoryStatus.QUARANTINED}:
            raise ValueError("Capture candidates must be reviewed before supersession")
        if old.status == MemoryStatus.SUPERSEDED:
            raise ValueError("Memory already superseded")
        if old.claim_subject and claim_value is None:
            raise ValueError("Superseding a structured claim requires the replacement claim_value")
        if not note.strip():
            raise ValueError("A verification note is required")
        replacement_start = (
            datetime.fromisoformat(valid_from.replace("Z", "+00:00"))
            if isinstance(valid_from, str) else
            valid_from or (datetime.now() if old.claim_subject else None)
        )
        replacement_end = (
            datetime.fromisoformat(valid_to.replace("Z", "+00:00"))
            if isinstance(valid_to, str) else valid_to
        )
        if replacement_end is not None and replacement_start is not None:
            Memory.model_validate({
                "content": "claim interval validation",
                "valid_from": replacement_start,
                "valid_to": replacement_end,
            })
        if old.claim_subject and old.claim_predicate and old.valid_to is None:
            proposed_end = replacement_start or datetime.now()
            old_snapshot = old.model_dump()
            old_snapshot["valid_to"] = proposed_end
            Memory.model_validate(old_snapshot)
        replacement = Memory(
            content=content, type=old.type, tags=old.tags, source="verified-replacement",
            file_paths=old.file_paths if file_paths is None else file_paths,
            symbols=old.symbols, salience=old.salience, supersedes=old.id,
            related_to=[old.id], verification_note=note.strip(),
            scope_type=old.scope_type, scope_id=old.scope_id,
            provenance={"source": "reviewed_replacement", "supersedes": old.id},
            trust_basis="human_reviewed", answer_slots=old.answer_slots.copy(),
            sensitivity=old.sensitivity,
            confidence=old.confidence,
            claim_confidence=claim_confidence,
            claim_subject=old.claim_subject,
            claim_predicate=old.claim_predicate,
            claim_value=claim_value,
            claim_environment=old.claim_environment,
            claim_state=("adopted" if old.type.value == "decision" or old.claim_subject
                         else old.claim_state),
            valid_from=replacement_start,
            valid_to=replacement_end,
            status=MemoryStatus.ACTIVE_VERIFIED,
        )
        if not replacement.file_paths:
            raise ValueError("Replacement requires linked evidence files")
        replacement.commit_sha = self._review_commit(old, commit, replacement.file_paths)
        repo = Repository(self.project_dir)
        replacement.evidence_branch = repo.current_context()["branch"]
        replacement.evidence_refs = repo.capture_evidence(
            replacement.commit_sha, replacement.file_paths, replacement.symbols
        )
        old.revisions.append(old.model_dump(mode="json", exclude={"revisions"}))
        if old.claim_subject and old.claim_predicate and old.valid_to is None:
            old.valid_to = replacement_start
        old.status = MemoryStatus.SUPERSEDED
        old.superseded_by = replacement.id
        old.updated_at = datetime.now()
        # Both records share a type/file. One atomic replacement avoids half a lifecycle transition.
        self.markdown.replace_with_successor(old, replacement)
        note_hash = "review-note-sha256:" + hashlib.sha256(note.strip().encode()).hexdigest()
        self.events.append(old.id, "superseded", reason=note_hash,
                           memory_type=old.type.value, status=old.status.value,
                           revision=len(old.revisions))
        self.events.append(replacement.id, "created_as_successor", reason=note_hash,
                           memory_type=replacement.type.value, status=replacement.status.value)
        self._index(old)
        self._index(replacement)
        return replacement
