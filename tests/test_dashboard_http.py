"""Start the actual local dashboard server and inspect it over HTTP."""

import http.client
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore


def test_live_dashboard_http(tmp_path):
    MarkdownManager(tmp_path).initialize_brain("HTTP inspection")
    memory = MemoryStore(tmp_path, enable_vectors=False).add("Authentication uses cookies")
    with socket.socket() as available:
        available.bind(("127.0.0.1", 0))
        port = available.getsockname()[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONUTF8"] = "1"
    log_path = tmp_path / "dashboard-server.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "oxmemory.dashboard", "--project", str(tmp_path),
             "--keyword-only", "--port", str(port)],
            env=env, stdout=log, stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 15
            while True:
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                try:
                    connection.request("GET", "/api/memories")
                    response = connection.getresponse()
                    assert response.status == 200
                    assert json.loads(response.read())[0]["id"] == memory.id
                    break
                except (ConnectionError, OSError):
                    if process.poll() is not None or time.monotonic() >= deadline:
                        raise AssertionError(log_path.read_text(encoding="utf-8"))
                    time.sleep(0.05)
                finally:
                    connection.close()
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            try:
                connection.request("GET", "/")
                response = connection.getresponse()
                assert response.status == 200
                assert b"Project memory" in response.read()
            finally:
                connection.close()
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
