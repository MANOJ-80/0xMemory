"""Real MCP SDK client test, with subprocess restart and lifecycle assertions."""

import asyncio
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from oxmemory.storage.markdown import MarkdownManager


def test_stdio_transport(tmp_path):
    run_stdio_lifecycle(tmp_path)


def test_stdio_anonymous_transport(tmp_path):
    from tests.stdio_anonymous import anonymous_stdio_client
    run_stdio_lifecycle(tmp_path, anonymous_stdio_client)


def run_stdio_lifecycle(tmp_path, transport=None):
    # No skip or print-only success: missing dependencies and protocol failures fail this test.
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client as sdk_stdio_client

    stdio_client = transport or sdk_stdio_client

    executable = shutil.which("git")
    if not executable:
        candidate = Path("C:/Program Files/Git/cmd/git.exe")
        executable = str(candidate) if candidate.exists() else None
    assert executable, "Git is required for the MCP lifecycle test"

    def git(*args):
        return subprocess.run(
            [executable, "-C", str(tmp_path), *args], check=True,
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()

    git("init")
    git("config", "user.name", "MCP Integration Test")
    git("config", "user.email", "test@example.invalid")
    git("config", "commit.gpgsign", "false")
    git("config", "core.hooksPath", "")
    evidence = tmp_path / "auth.py"
    evidence.write_text('AUTH = "jwt"\n', encoding="utf-8")
    git("add", "auth.py")
    git("commit", "-m", "JWT authentication")
    MarkdownManager(tmp_path).initialize_brain("MCP lifecycle")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "oxmemory", "serve", str(tmp_path)],
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
             "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1",
             **{key: os.environ[key] for key in
                ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HOME", "HF_HUB_CACHE")
                if key in os.environ}},
    )

    async def call(session, name, arguments):
        result = await session.call_tool(name, arguments)
        assert not result.is_error, result
        data = json.loads(next(item.text for item in result.content if item.type == "text"))
        assert "error" not in data, data
        return data

    async def exercise():
        async with asyncio.timeout(180):
            async with stdio_client(parameters) as (read, write):
                async with ClientSession(read, write) as session:
                    initialized = await session.initialize()
                    assert initialized.server_info.name == "0xmemory"
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    assert {"remember", "recall", "observe_commit", "verify_memory",
                            "supersede_memory"} <= names
                    resources = await session.list_resources()
                    assert any(str(r.uri).rstrip("/") == "brain://context"
                               for r in resources.resources)
                    context = await session.read_resource("brain://context")
                    assert "MCP lifecycle" in context.contents[0].text
                    prompts = await session.list_prompts()
                    assert any(p.name == "project_context" for p in prompts.prompts)
                    prompt = await session.get_prompt("project_context")
                    assert "MCP lifecycle" in prompt.messages[0].content.text
                    stored = await call(session, "remember", {
                        "content": "Authentication uses JWT", "type": "decision",
                        "file_paths": ["auth.py"], "commit_sha": "HEAD",
                    })
                    old_id = stored["id"]
                    recalled = await call(session, "recall", {"query": "Authentication"})
                    assert [m["id"] for m in recalled["memories"]] == [old_id]
                    evidence.write_text('AUTH = "cookie"\n', encoding="utf-8")
                    git("add", "auth.py")
                    git("commit", "-m", "Cookie authentication")
                    observed = await call(session, "observe_commit", {"commit": "HEAD"})
                    assert observed["affected"][0]["id"] == old_id
                    assert not (await call(session, "recall", {
                        "query": "Authentication",
                    }))["memories"]
                    replacement = await call(session, "supersede_memory", {
                        "id": old_id, "content": "Authentication uses cookie sessions",
                        "commit": "HEAD", "note": "Reviewed AUTH in auth.py",
                    })
                    new_id = replacement["id"]
            # A new server process proves persistence rather than just in-process state.
            async with stdio_client(parameters) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    recalled = await call(session, "recall", {
                        "query": "Authentication", "file_paths": ["auth.py"],
                    })
                    assert [m["id"] for m in recalled["memories"]] == [new_id]
                    history = await call(session, "list", {})
                    old = next(m for m in history["memories"] if m["id"] == old_id)
                    assert old["status"] == "superseded"
                    assert old["superseded_by"] == new_id

    asyncio.run(exercise())
