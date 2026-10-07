"""ASGI integration and evaluation checks using the standard-library test runner."""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from oxmemory.dashboard import create_dashboard
from oxmemory.evaluation import metrics, run_evaluation
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore


async def request(app, path, method="GET", body=None, origin=None, query=""):
    messages = []
    sent = False

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": json.dumps(body).encode() if body else b"",
                    "more_body": False}
        await asyncio.Event().wait()

    async def send(message):
        messages.append(message)

    headers = [(b"host", b"testserver"), (b"content-type", b"application/json")]
    if origin:
        headers.append((b"origin", origin.encode()))
    scope = {"type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
             "http_version": "1.1", "method": method, "scheme": "http", "path": path,
             "raw_path": path.encode(), "query_string": query.encode(), "root_path": "",
             "headers": headers, "client": ("127.0.0.1", 12345), "server": ("testserver", 80)}
    await asyncio.wait_for(app(scope, receive, send), timeout=5)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    content = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, content


class DashboardTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        MarkdownManager(self.root).initialize_brain("Dashboard")
        self.store = MemoryStore(self.root, enable_vectors=False)
        self.memory = self.store.add("Use cookie authentication", file_paths=["auth.py"])
        self.app = create_dashboard(self.root, enable_vectors=False)

    async def test_inspection_and_search_routes(self):
        status, body = await request(self.app, "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Project memory", body)
        status, body = await request(self.app, "/api/memories")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)[0]["id"], self.memory.id)
        status, body = await request(self.app, "/api/recall", query="query=cookie&file=auth.py")
        self.assertEqual(status, 200)
        self.assertIn("cookie", json.loads(body)["context"])

    async def test_bad_review_is_rejected_without_mutation(self):
        status, _ = await request(self.app, f"/api/memories/{self.memory.id}/review", "POST",
                                  {"note": ""})
        self.assertEqual(status, 422)
        self.assertEqual(self.store.get(self.memory.id).content, self.memory.content)

    async def test_cross_origin_mutation_rejected(self):
        status, _ = await request(self.app, "/api/observe", "POST", {"commit": "HEAD"},
                                  origin="https://unrelated.example")
        self.assertEqual(status, 403)

    async def test_invalid_budget_returns_useful_error(self):
        status, body = await request(self.app, "/api/recall", query="query=cookie&budget=-1")
        self.assertEqual(status, 400)
        self.assertIn("token_budget", json.loads(body)["detail"])


class EvaluationTests(unittest.TestCase):
    def test_metrics_with_known_ranking(self):
        result = metrics(["wrong", "right"], {"right"}, {"wrong"})
        self.assertEqual(result["precision"], 0.5)
        self.assertEqual(result["recall"], 1)
        self.assertEqual(result["reciprocal_rank"], 0.5)
        self.assertEqual(result["stale_fraction"], 0.5)
        self.assertTrue(metrics([], set(), set())["correct_abstention"])

    def test_evaluation_labels_proxy_and_filters_stale_memories(self):
        result = run_evaluation()
        self.assertEqual(result["mode"], "keyword_only_proxy")
        self.assertEqual(len(result["results"]), 12)
        self.assertEqual(result["summary"]["enhanced_memory"]["stale_fraction"], 0)
        self.assertGreater(result["summary"]["basic_memory"]["stale_fraction"], 0)


if __name__ == "__main__":
    unittest.main()
