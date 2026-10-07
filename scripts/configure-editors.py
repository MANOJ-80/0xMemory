"""Create project-local MCP configs using the Python running this script."""

import argparse
import json
import sys
from pathlib import Path


def configure(project: Path, offline_models: bool = False):
    project = project.expanduser().resolve()
    if not (project / ".0xmemory" / "brain.md").is_file():
        raise ValueError("Initialize this project's brain first with oxmemory init")
    # Do not resolve the interpreter symlink: Linux venv/bin/python may point at
    # the system binary, but invoking that system path would lose the environment.
    interpreter = Path(sys.executable).absolute().as_posix()
    env = {"PYTHONUTF8": "1"}
    if offline_models:
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    entry = {
        "command": interpreter,
        "args": ["-m", "oxmemory", "serve", project.as_posix()],
        "env": env,
    }
    documents = {
        ".vscode/mcp.json": {"servers": {"0xmemory-dodo": {"type": "stdio", **entry}}},
        ".cursor/mcp.json": {"mcpServers": {"0xmemory-dodo": entry}},
        ".agents/mcp_config.json": {"mcpServers": {"0xmemory-dodo": entry}},
    }
    existing = [name for name in documents if (project / name).exists()]
    if existing:
        raise FileExistsError(f"Configs already exist; merge manually: {', '.join(existing)}")
    for name, document in documents.items():
        path = project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        print(f"Created {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--offline-models", action="store_true")
    args = parser.parse_args()
    try:
        configure(args.project, args.offline_models)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
