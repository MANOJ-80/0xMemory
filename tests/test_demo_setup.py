"""Setup boundary tests: preserve configs, isolate evidence, verify real MCP status."""

import asyncio
import json
import runpy
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
config = runpy.run_path(str(ROOT / "scripts/configure-editors.py"))
setup = runpy.run_path(str(ROOT / "scripts/demo_setup.py"))


def brain(project):
    (project / ".0xmemory").mkdir(parents=True)
    (project / ".0xmemory/brain.md").write_text("# test", encoding="utf-8")


def test_merge_preserves_other_clients_comments_and_is_idempotent(tmp_path):
    brain(tmp_path)
    (tmp_path / ".vscode").mkdir()
    original_json = {"inputs": [{"id": "token"}], "servers": {"other": {"command": "other"}}}
    json_path = tmp_path / ".vscode/mcp.json"
    json_path.write_text(json.dumps(original_json), encoding="utf-8")
    (tmp_path / ".codex").mkdir()
    toml_path = tmp_path / ".codex/config.toml"
    original_toml = '# Keep my settings\nmodel = "my-model"\n[mcp_servers.other]\ncommand="other"\n'
    toml_path.write_text(original_toml, encoding="utf-8")
    config["configure"](tmp_path, True, config["CLIENTS"])
    document = json.loads(json_path.read_text())
    assert document["inputs"] == original_json["inputs"]
    assert document["servers"]["other"] == original_json["servers"]["other"]
    assert toml_path.read_text().startswith(original_toml)
    codex = tomllib.loads(toml_path.read_text())["mcp_servers"]["0xmemory-todo"]
    assert codex["command"] == Path(sys.executable).absolute().as_posix()
    assert codex["args"][-1] == tmp_path.as_posix()
    assert codex["env"]["HF_HUB_OFFLINE"] == "1"
    saved = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    config["configure"](tmp_path, True, config["CLIENTS"])
    assert saved == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert len(list(tmp_path.rglob("*.backup-*"))) == 2


def test_conflict_preflight_leaves_all_files_unchanged(tmp_path):
    brain(tmp_path)
    (tmp_path / ".codex").mkdir()
    path = tmp_path / ".codex/config.toml"
    original = '[mcp_servers.0xmemory-todo]\ncommand="something-else"\n'
    path.write_text(original)
    with pytest.raises(ValueError, match="Conflicting"):
        config["configure"](tmp_path)
    assert not (tmp_path / ".vscode").exists()
    assert path.read_text() == original


def test_invalid_config_is_not_rewritten(tmp_path):
    brain(tmp_path)
    (tmp_path / ".vscode").mkdir()
    path = tmp_path / ".vscode/mcp.json"
    path.write_text("{ // comment")
    with pytest.raises(ValueError):
        config["configure"](tmp_path)
    assert path.read_text() == "{ // comment"
    assert not (tmp_path / ".codex").exists()


def test_missing_brain_and_existing_project_are_not_mutated(tmp_path):
    with pytest.raises(ValueError, match="Initialize"):
        config["configure"](tmp_path)
    with pytest.raises(ValueError, match="already exists"):
        setup["fresh_project"](tmp_path)
    with pytest.raises(ValueError, match="outside"):
        setup["fresh_project"](ROOT / "never-create-demo")
    assert not list(tmp_path.iterdir())


def test_handoff_contains_actual_commands_outside_app(tmp_path):
    app = tmp_path / "app with spaces"
    app.mkdir()
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    setup["handoff"](app, Path(sys.executable), evidence)
    prompt = (evidence / "DEMO_FLOW.md").read_text(encoding="utf-8")
    assert "{{PROJECT}}" not in prompt and "{{TEST_COMMAND}}" not in prompt
    assert str(Path(sys.executable)) in prompt
    assert "app with spaces" in prompt
    assert not list(app.iterdir())


def test_fresh_starter_and_read_only_mcp_smoke(tmp_path):
    app = tmp_path / "todo with spaces"
    shutil.copytree(
        ROOT / "examples/todo-starter", app, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    subprocess.run([sys.executable, "-m", "unittest", "-v"], cwd=app, check=True)
    subprocess.run(
        [sys.executable, "-m", "oxmemory", "init", "--name", app.name, "--local"],
        cwd=app,
        check=True,
    )
    config["configure"](app, True)
    before = {p: p.read_bytes() for p in (app / ".0xmemory").rglob("*.md")}
    smoke = runpy.run_path(str(ROOT / "scripts/check-demo-mcp.py"))
    result = asyncio.run(smoke["check"](app, "anonymous"))
    assert result["status"]["total_memories"] == 0
    assert len(result["tools"]) == 10
    assert before == {p: p.read_bytes() for p in (app / ".0xmemory").rglob("*.md")}
