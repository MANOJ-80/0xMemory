"""Small append-only, content-minimizing lifecycle event ledger."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from oxmemory.core.config import get_brain_path


class EventLedger:
    """Append tamper-evident lifecycle metadata without duplicating memory text."""

    def __init__(self, project_dir: Path):
        self.path = get_brain_path(project_dir) / "events.jsonl"

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        events, previous = [], "0" * 64
        for line_no, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            event = json.loads(line)
            digest = event.pop("event_hash", None)
            if event.get("previous_hash") != previous:
                raise ValueError(f"Event ledger chain is broken at line {line_no}")
            expected = hashlib.sha256(json.dumps(event, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if digest != expected:
                raise ValueError(f"Event ledger checksum failed at line {line_no}")
            event["event_hash"] = digest
            events.append(event)
            previous = digest
        return events

    def append(self, memory_id: str, action: str, *, actor: str = "local-user",
               reason: str | None = None, memory_type: str | None = None,
               status: str | None = None, revision: int | None = None,
               details: dict | None = None) -> dict:
        events = self.read()
        event = {
            "event_id": f"evt-{uuid4().hex[:12]}",
            "at": datetime.now(timezone.utc).isoformat(),
            "memory_id": memory_id,
            "action": action,
            "actor": actor,
            "reason": reason,
            "memory_type": memory_type,
            "status": status,
            "revision": revision,
            "details": details or {},
            "previous_hash": events[-1]["event_hash"] if events else "0" * 64,
        }
        event["event_hash"] = hashlib.sha256(
            json.dumps(event, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return event

    def status(self) -> dict:
        try:
            events = self.read()
            return {"available": True, "events": len(events), "chain_valid": True,
                    "last_event_at": events[-1]["at"] if events else None}
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {"available": True, "events": None, "chain_valid": False, "error": str(exc)}
