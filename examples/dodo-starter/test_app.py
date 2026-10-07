import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app


class TodoTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.data = Path(self.directory.name)
        self.client = self.enterContext(TestClient(create_app(self.data)))

    def test_create_and_reload(self):
        response = self.client.post("/api/tasks", json={"title": "Prepare review"})
        self.assertEqual(response.status_code, 201)
        created = response.json()
        with TestClient(create_app(self.data)) as restarted:
            self.assertEqual(restarted.get("/api/tasks").json(), [created])

    def test_complete_and_delete(self):
        task = self.client.post("/api/tasks", json={"title": "Record demo"}).json()
        path = "/api/tasks/" + task["id"]
        updated = self.client.patch(path, json={"completed": True})
        self.assertTrue(updated.json()["completed"])
        self.assertEqual(self.client.delete(path).status_code, 204)
        self.assertEqual(self.client.get("/api/tasks").json(), [])

    def test_invalid_titles(self):
        for title in ["", "   ", "a" * 201]:
            self.assertEqual(self.client.post("/api/tasks", json={"title": title}).status_code, 422)

    def test_missing_task(self):
        self.assertEqual(self.client.patch("/api/tasks/missing", json={"completed": True}).status_code, 404)
        self.assertEqual(self.client.delete("/api/tasks/missing").status_code, 404)

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Dodo", response.text)


if __name__ == "__main__":
    unittest.main()
