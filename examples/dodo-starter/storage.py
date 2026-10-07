"""Small local JSON task store for the initial demonstration version."""

import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from uuid import uuid4


class TaskStore:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "tasks.json"
        self.lock = RLock()

    def list(self):
        with self.lock:
            if not self.path.exists():
                return []
            return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, tasks):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(tasks, stream, indent=2, ensure_ascii=False)
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def add(self, title):
        with self.lock:
            tasks = self.list()
            task = {"id": uuid4().hex, "title": title, "completed": False}
            tasks.append(task)
            self._save(tasks)
            return task

    def complete(self, task_id, completed):
        with self.lock:
            tasks = self.list()
            for task in tasks:
                if task["id"] == task_id:
                    task["completed"] = completed
                    self._save(tasks)
                    return task
            raise KeyError(task_id)

    def delete(self, task_id):
        with self.lock:
            tasks = self.list()
            retained = [task for task in tasks if task["id"] != task_id]
            if len(retained) == len(tasks):
                raise KeyError(task_id)
            self._save(retained)
