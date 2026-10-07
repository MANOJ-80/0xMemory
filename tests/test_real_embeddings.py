"""Actual ChromaDB/embedding persistence check; never substitutes a mock or fallback."""

import os
import subprocess
import sys
from pathlib import Path


def test_real_embedding_update_and_retrieval(tmp_path):
    # A separate process releases Chroma's SQLite handles before Windows temp cleanup.
    source = '''
import sys
from pathlib import Path
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore
from oxmemory.storage.vector_store import VectorStore

root = Path(sys.argv[1])
MarkdownManager(root).initialize_brain("Real embedding test")
store = MemoryStore(root)
auth = store.add("Authentication uses JWT tokens")
store.add("The reporting database stores invoices")
vectors = store.vector_store
assert vectors is not None, "Real vector backend unavailable"
assert vectors.count() == 2, "Memory ingestion silently failed to index"
assert len(vectors._embed(["authentication"])[0]) == 384
store.update(auth.id, "Authentication uses cookie sessions")
assert vectors.get(auth.id)["content"] == "Authentication uses cookie sessions"
fresh = VectorStore(root)
assert fresh.search("Authentication uses cookie sessions", limit=1)[0]["id"] == auth.id
store.delete(auth.id)
assert fresh.get(auth.id) is None
print("REAL_EMBEDDINGS_PASSED")
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    result = subprocess.run(
        [sys.executable, "-c", source, str(tmp_path)], env=env,
        capture_output=True, text=True, encoding="utf-8", timeout=300,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "REAL_EMBEDDINGS_PASSED" in result.stdout
