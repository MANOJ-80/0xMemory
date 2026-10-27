"""Merge project-local MCP settings without replacing conflicting server entries."""

import argparse
import json
import os
import sys
import tempfile
import tomllib
from pathlib import Path

CLIENTS = ("vscode", "codex", "cursor", "antigravity")
SERVER = "0xmemory-todo"


def configure(project, offline_models=False, clients=("vscode", "codex")):
    project = Path(project).expanduser().resolve()
    if not (project / ".0xmemory/brain.md").is_file():
        raise ValueError("Initialize this project brain first with oxmemory init")
    if not clients or set(clients) - set(CLIENTS):
        raise ValueError(f"Choose clients from {CLIENTS}")
    # Do not resolve a Linux venv interpreter symlink to its system target.
    entry = dict(
        command=Path(sys.executable).absolute().as_posix(),
        args=["-m", "oxmemory", "serve", project.as_posix()],
        env={"PYTHONUTF8": "1"},
    )
    if offline_models:
        entry["env"].update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    locations = {
        "vscode": (".vscode/mcp.json", "servers"),
        "cursor": (".cursor/mcp.json", "mcpServers"),
        "antigravity": (".agents/mcp_config.json", "mcpServers"),
    }
    changes = []
    for client in dict.fromkeys(clients):
        if client == "codex":
            path = project / ".codex/config.toml"
            before = path.read_text(encoding="utf-8-sig") if path.exists() else ""
            document = tomllib.loads(before)
            desired = {**entry, "startup_timeout_sec": 60, "tool_timeout_sec": 120}
            existing = document.get("mcp_servers", {}).get(SERVER)
            if existing == desired:
                continue
            if existing is not None:
                raise ValueError(f"Conflicting {SERVER} in {path}; merge manually")
            after = before.rstrip() + f"\n\n[mcp_servers.{SERVER}]\n"
            for key, value in desired.items():
                if key != "env":
                    after += f"{key} = {json.dumps(value, ensure_ascii=False)}\n"
            after += f"\n[mcp_servers.{SERVER}.env]\n"
            after += "".join(f"{k} = {json.dumps(v)}\n" for k, v in entry["env"].items())
            tomllib.loads(after)
        else:
            name, wrapper = locations[client]
            path = project / name
            before = path.read_text(encoding="utf-8-sig") if path.exists() else ""
            document = json.loads(before) if before else {}
            servers = document.setdefault(wrapper, {})
            desired = {"type": "stdio", **entry} if client == "vscode" else entry
            if servers.get(SERVER) == desired:
                continue
            if SERVER in servers:
                raise ValueError(f"Conflicting {SERVER} in {path}; merge manually")
            servers[SERVER] = desired
            after = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
        changes.append((path, after))
    # Preflight every config before any writes; keep backups of existing files.
    for path, after in changes:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix=path.name + ".backup-", delete=False
            ) as backup:
                backup.write(path.read_bytes())
            print(f"Backup: {backup.name}")
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as temporary:
            temporary.write(after)
        os.replace(temporary.name, path)
        print(f"Configured {path}")
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--offline-models", action="store_true")
    parser.add_argument("--clients", nargs="+", choices=CLIENTS, default=["vscode", "codex"])
    args = parser.parse_args()
    try:
        configure(args.project, args.offline_models, args.clients)
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
