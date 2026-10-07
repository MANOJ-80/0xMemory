# testDodoapp

This is the reusable JSON baseline. Copy this directory, including dotfiles, into
a separate sibling `testDodoapp` directory before running the experiment. See
`START_HERE.md` (Windows) or `UBUNTU_SETUP.md` (Ubuntu) in the 0xMemory engine
repository for initialization and MCP setup.
The commands below assume `0xMemory` and `testDodoapp` are sibling directories.

A small local todo application: add tasks, mark them complete, and delete them.
Tasks survive application restarts. Initial storage is `data/tasks.json`.

From this directory, using the existing adjacent Python environment:

```powershell
..\0xMemory\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8090
```

Open http://127.0.0.1:8090. Stop the application with Ctrl+C.

On Ubuntu/Bash, start the app with:

```bash
../0xMemory/.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8090
```

Run the API and persistence tests:

```powershell
..\0xMemory\.venv\Scripts\python.exe -m unittest -v
```

On Ubuntu/Bash, run the tests with:

```bash
../0xMemory/.venv/bin/python -m unittest -v
```

`app.py` defines the API and serves `index.html`; `storage.py` owns persistence.
This is a local demonstration application; use one application process.

After following START_HERE, its separate memory store lives in `.0xmemory/`.
VS Code Copilot configuration is generated in `.vscode/mcp.json` under the name
`0xmemory-dodo`; Cursor and Antigravity configurations are generated too. These
local files and the brain are intentionally not included in the starter template.
