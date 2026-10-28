# One-command To-do demo setup

Use this guide first. Manual Windows and Ubuntu guides remain available for
troubleshooting. New demos are **testTodoapp**, with server **0xmemory-todo**.
Older testDodoapp folders and recorded IDs/results are historical evidence; do
not rename them or reuse their memories for a fresh experiment.

## 1. Clone and install the prerequisites

Install Git and Python 3.12 (3.11 is also accepted). Install/sign in to VS Code
with GitHub Copilot, Codex CLI, or the desktop client you plan to test. The scripts
do not install editors, sign you in, change trust settings, or install system
packages. They install engine dependencies inside the engine's `.venv`.

On Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv ca-certificates
```

For other Ubuntu versions, see [Python alternatives](UBUNTU_SETUP.md#2-install-ubuntu-prerequisites).
Then clone in your chosen parent folder on either OS:

```text
git clone https://github.com/MANOJ-80/0xMemory.git
cd 0xMemory
git switch architecture/evidence-grounded-memory
```

The architecture branch must be published for a fresh clone to fetch it. If it
is still local, use the existing checkout already on that branch or wait for
the maintainer to publish it; do not install `main` and assume it contains the
architecture changes.

The default layout is `0xMemory/` and `testTodoapp/` side by side. Do not clone or
run this inside an existing app's repository. Internet is needed for the first
package installation and model download; allow time and disk space for PyTorch.

## 2. Run ONE setup command for your OS

**Windows PowerShell**, inside the engine clone:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-demo.ps1
```

This process-only execution policy does not change your global policy.

**Ubuntu Bash**, inside the engine clone:

```bash
bash scripts/setup-demo.sh
```

No venv activation or manual JSON editing is needed. Defaults configure **VS Code
Copilot and Codex CLI/Desktop**. Both commands:

1. Check Git and Python; create/reuse the engine venv and install dependencies.
2. Run the deterministic, offline architecture memory-system smoke check.
3. Check packages and download/check the real embedding model.
4. Copy the JSON To-do starter into a fresh sibling app repository.
5. Create its first local commit using a per-command demo identity; no push.
6. Initialize its named memory brain and run the five starter app tests.
7. Generate local VS Code JSON and Codex TOML with absolute engine/app paths.
8. Use a real MCP SDK client for tool discovery and zero-memory status checks.
9. Print the app folder and a separate evidence folder containing logs, results,
   exact prompts, a report template, and an app launcher.

Setup stops on any failure. `setup-result.json` records PASS/FAIL and completed
steps. PASS means preparation succeeded; separate-chat and editor tests are still
NOT RUN. The smoke check does not add memories or migrate tasks.

## 3. Open the app in your client

Open **testTodoapp**, not the engine or parent folder. Use one active MCP client
at a time against this brain. Do not launch a separate `oxmemory serve` terminal;
the client starts its own stdio process. Account sign-in and trust stay manual.

### VS Code + GitHub Copilot

Open the app folder, select Agent mode, run **MCP: List Servers**, and start
`0xmemory-todo`. Handle the trust prompt and enable its tools. The settings are
in the app's `.vscode/mcp.json`. For the **Codex extension inside VS Code**, use
the Codex configuration below instead; Copilot JSON does not configure Codex.

### Codex CLI

From the app folder, start `codex`, sign in if needed, and trust the project only
after reviewing it. Restart the session if the config was generated while it was
open. Use `/mcp` to check connection/tools, then run the connection prompt below.
`codex mcp list` can inspect configuration, but a listing alone is not proof of
successful tool invocation.

### Codex desktop / Codex in ChatGPT desktop

Open a local task/project rooted at the same app directory and accept its trust
prompt. Restart the client/session after configuration. Check MCP servers in
Settings or `/mcp`, according to your installed build, then invoke status.
The generated `.codex/config.toml` is project-scoped. The official documentation
states that trusted project MCP configuration is shared across desktop, CLI,
and the IDE extension. [Official OpenAI MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

Use local execution in the OS that owns the venv. A remote/cloud task cannot
execute your local Python path. This guide does not assume desktop availability
on every Ubuntu release: use Codex CLI on Ubuntu if your desktop build is not
available. On WSL, use a Linux clone/venv and a client running in that Linux
context; Windows paths and Linux paths are not interchangeable.

No user-global Codex configuration or trust/approval settings are changed.
If organizational policy blocks MCP, report the policy message rather than
claiming setup succeeded inside that client.

### First agent prompt

```text
Use 0xmemory-todo status. Report the project, brain path, and memory counts.
Expect testTodoapp and zero memories. Stop if the project differs.
```

For a custom project folder, substitute its basename. Expand the actual tool
result. This is the manual client connection check missing from automated setup.

## 4. Start the app and test the lifecycle

The printed evidence folder contains `run-app.ps1` (Windows) or `run-app.sh`
(Ubuntu). Invoke it using the appropriate shell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\YOUR\EVIDENCE_FOLDER\run-app.ps1"
```

```bash
bash "/your/evidence-folder/run-app.sh"
```

Open http://127.0.0.1:8090. Keep the terminal running; Ctrl+C stops it. Then follow
**the generated `DEMO_FLOW.md`** in the evidence folder. Its paths and test command
are already filled in:

Remember JSON rationale → new-chat recall → SQLite migration → local commit →
observe and flag for review → inspect evidence and supersede → another new-chat
recall → optional client switch. Changed evidence does not automatically prove a
claim false; review-required memories can still appear with a warning. The shared
[prompt template](DEMO_FLOW.md) is also in the repo.

Record IDs, SHAs, screenshots, client versions, and actual results in the generated
`TEST_REPORT.md`. Keep this evidence outside the app so recall tests cannot simply
read the expected answer from their workspace.

## Options and repeat runs

| Purpose | PowerShell option | Bash option |
| --- | --- | --- |
| Fresh app location | `-Project "../testTodoapp2"` | `--project "../testTodoapp2"` |
| Existing installed environment | `-SkipInstall` | `--skip-install` |
| Already cached model | `-OfflineModels` | `--offline-models` |
| Full engine suite, demo, semantic evaluation | `-FullVerify` | `--full-verify` |
| Only VS Code | `-Clients vscode` | `--clients vscode` |
| Only Codex | `-Clients codex` | `--clients codex` |
| Interpreter selection | `-PythonBin "C:\path\python.exe"` | `PYTHON_BIN=/path/python3.12 bash ...` |

For multiple PowerShell clients, invoke the script directly as
`& .\scripts\setup-demo.ps1 -Clients vscode,codex,cursor,antigravity` in a shell
whose policy permits local scripts. Bash uses `--clients vscode codex cursor antigravity`.
Cursor and Antigravity remain optional; see [editor setup](EDITOR_SETUP.md).

Existing app folders are never reset. Choose a new sibling app name for each
fresh run. After a failure, logs and any partially created app remain for diagnosis;
fix the failure and choose a new app path if it already exists. Existing engine
venvs are reused, but a Windows venv cannot be reused on Ubuntu.

Config generation preserves unrelated servers/settings, backs up modified config
files, and is a no-op for matching entries. A conflicting `0xmemory-todo` entry
fails before any config is written. JSON must be strict JSON; comments/trailing
commas require a manual merge. Codex TOML comments are preserved. For an existing
initialized project, run the config helper separately from the engine:

```powershell
.\.venv\Scripts\python.exe scripts/configure-editors.py --project "../testTodoapp" --offline-models
```

```bash
.venv/bin/python scripts/configure-editors.py --project "../testTodoapp" --offline-models
```

## Failure diagnostics

- Missing Python/venv: install the supported interpreter and matching venv package.
- Windows `WinError 4551` loading a PyTorch DLL: Application Control blocked the
  installed binary. Record the error and resolve it through the machine administrator
  or use an allowed test machine; setup does not disable that policy.
- Download/network failure: resolve access, rerun installation; offline flags only
  work with an installed environment and cached model.
- Existing app: choose a new path; no deletion is necessary.
- MCP native launcher pipe errors in a restricted Windows sandbox: retry in a
  normal terminal. An explicit diagnostic `-McpTransport anonymous` /
  `--mcp-transport anonymous` uses the existing ordinary-pipe adapter with the real
  MCP SDK. It is recorded as such and does not prove the native launcher or editor
  worked. FullVerify still runs every test without exclusions.
- Config generated but client cannot see it: open the correct app, trust it,
  restart, inspect MCP logs, and check the client executes on the same OS.
- Setup result missing: prerequisite checks can fail before an evidence folder is
  created; read the terminal error. Do not treat partial output as PASS.

See [integration status](INTEGRATION_STATUS.md) for what was actually tested.
