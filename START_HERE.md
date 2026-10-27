# From a fresh clone to a complete MCP memory demonstration

**Recommended: [one-command To-do setup](QUICKSTART_DEMO.md)** for Windows/Ubuntu, VS Code Copilot, and Codex CLI/Desktop. The detailed manual steps below remain available for troubleshooting.

Audience: a teammate who has never installed this project. Follow the numbered steps in order. This guide uses **Windows PowerShell and Python 3.12**, matching the completed team test.

**Using Ubuntu? Follow [UBUNTU_SETUP.md](UBUNTU_SETUP.md) instead.** It contains the complete Bash installation, editor configuration, fresh-app test, and memory lifecycle prompts. Ubuntu runtime validation is pending; Windows results do not establish a Linux pass.

**Terminal blocks go in PowerShell. Agent prompt blocks go in your editor's AI chat. Send one agent prompt at a time and wait for its result.** “New chat” means an empty conversation, not another message in the existing conversation.

## Contents

1. [What you will test](#1-what-you-will-test)
2. [Prerequisites and clone](#2-prerequisites-and-clone)
3. [Create the Python environment](#3-create-the-python-environment)
4. [Download embeddings and verify the engine](#4-download-embeddings-and-verify-the-engine)
5. [Create a separate fresh To-do project](#5-create-a-separate-fresh-to-do-project)
6. [Generate local editor configurations](#6-generate-local-editor-configurations)
7. [Connect your editor](#7-connect-your-editor)
8. [Run and check the application](#8-run-and-check-the-application)
9. [Remember the JSON decision](#9-remember-the-json-decision)
10. [Recall in a new chat](#10-recall-in-a-new-chat)
11. [Migrate the app to SQLite](#11-migrate-the-app-to-sqlite)
12. [Commit and observe the change](#12-commit-and-observe-the-change)
13. [Review and supersede the old decision](#13-review-and-supersede-the-old-decision)
14. [Recall the current decision in another new chat](#14-recall-the-current-decision-in-another-new-chat)
15. [Switch editors and inspect history](#15-switch-editors-and-inspect-history)
16. [Record results and repeat safely](#16-record-results-and-repeat-safely)
17. [Troubleshooting](#17-troubleshooting)
18. [macOS and Linux notes](#18-macos-and-linux-notes)
19. [Maintainer handoff before a friend clones](#19-maintainer-handoff-before-a-friend-clones)

## 1. What you will test

```text
VS Code Copilot / Antigravity / Cursor (one at a time)
                         |
                    MCP over stdio
                         |
          0xMemory/.venv/Scripts/python.exe
                         |
          testTodoapp/.0xmemory/   <-- decisions and history
                         |
          testTodoapp Git commits <-- supporting code evidence

Browser --> http://127.0.0.1:8090 --> To-do app --> data/tasks.json
                                                 later tasks.db
```

The memory engine and application are **separate repositories**. The engine supplies Python code; the final argument to `serve` chooses the application whose memories are read and written. MCP uses subprocess pipes, not the application's HTTP port.

The successful flow is:

| Stage | Old JSON decision | New SQLite decision | Normal recall |
| --- | --- | --- | --- |
| Initial setup | Absent | Absent | No project memories |
| Remember | Active | Absent | JSON decision |
| Commit code, before observation | Still active | Absent | Can still return JSON |
| Explicitly observe commit | Stale | Absent | Excludes old decision |
| Review and supersede | Superseded | Active | SQLite decision |
| New chat/server restart | Preserved as history | Active | SQLite decision |

Memory IDs and Git SHAs are generated for your run. Never copy the team run's IDs into your own tool calls.

## 2. Prerequisites and clone

Install Git, Python 3.12, and at least one editor with a working AI agent account. Python 3.11 is declared supported, but the verified Windows setup uses 3.12. You do not need Node.js, Docker, a database service, Ollama, or a cloud API key for this remember/recall demonstration. The editor's agent still needs its own account/network access; local memory does not make Copilot or other hosted agents offline.

Open PowerShell and check:

```powershell
git --version
py -3.12 --version
```

If either is missing, install it and reopen PowerShell so PATH refreshes. Python packages and the embedding model need internet for first-time installation. Use a new directory, separate from any previous experiment:

```powershell
$demoRoot = Join-Path $env:USERPROFILE 'Desktop\MemoryLayerDemo'
New-Item -ItemType Directory -Force -Path $demoRoot | Out-Null
Set-Location $demoRoot
git clone https://github.com/MANOJ-80/0xMemory.git
if ($LASTEXITCODE -ne 0) { throw 'Clone failed; stop here.' }
$engineRoot = Join-Path $demoRoot '0xMemory'
Set-Location $engineRoot
git rev-parse HEAD
Test-Path .\examples\todo-starter\storage.py
Test-Path .\scripts\verify-local.ps1
```

Record the engine commit SHA. Both `Test-Path` results must be `True`. If not, ask the maintainer for the branch/commit containing this handoff and check it out. Do not improvise around missing lifecycle code. **Local changes on the maintainer's computer are not included in a GitHub clone until committed and pushed.** See section 19.

If the maintainer gave you a branch name, use `git switch BRANCH_NAME` after cloning, then rerun these checks. Replace the placeholder with the supplied name.

## 3. Create the Python environment

Run in the cloned `0xMemory` directory:

```powershell
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
$enginePython = Join-Path $engineRoot '.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
& $enginePython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed.' }
& $enginePython -m pip install -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $enginePython -m pip check
& $enginePython -m oxmemory --help
```

Expected: no broken requirements and the CLI command list, including `memory`. Editable installation means this environment imports code from your clone. Do not substitute `pip install oxmemory` from the package index: it may not contain this repository's lifecycle changes.

These commands call the environment's Python directly, so activation is unnecessary.
This also avoids PowerShell activation-policy errors. Optional activation from the
engine directory is `.\.venv\Scripts\Activate.ps1`; the guide does not rely on it.

The declared dependencies include local embedding libraries and can take time/disk space to install. Save installed versions for the report:

```powershell
& $enginePython -m pip freeze | Set-Content -Encoding utf8 (Join-Path $demoRoot 'installed-packages.txt')
```

Dependencies are version ranges, not a fully locked environment. Record versions rather than assuming a future install is identical to the team's tested install.

## 4. Download embeddings and verify the engine

First-time setup must allow downloads. In this terminal:

```powershell
$env:HF_HUB_OFFLINE = '0'
$env:TRANSFORMERS_OFFLINE = '0'
& $enginePython -c "from sentence_transformers import SentenceTransformer; m=SentenceTransformer('all-MiniLM-L6-v2'); print(m.encode(['memory setup check']).shape)"
if ($LASTEXITCODE -ne 0) { throw 'Embedding model preparation failed.' }
```

Expected shape: `(1, 384)`. This explicitly checks the real local embedding model; a successful CLI help command alone does not.

Now run the complete verifier from the engine directory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-local.ps1 -SkipInstall -OfflineModels
if ($LASTEXITCODE -ne 0) { throw 'Verification failed; inspect the first error.' }
```

This execution-policy setting applies to the launched PowerShell process; no permanent policy change is needed. `-SkipInstall` is appropriate because step 3 installed dependencies. `-OfflineModels` is appropriate only after the model was cached successfully. If package installation is incomplete, omit `-SkipInstall`; if model downloads are still required, omit `-OfflineModels` and ensure offline flags are not set to `1`.

Expected: **all collected tests pass**, then a PASS line covering dependencies,
CLI, tests, the real MCP client, embeddings, and semantic evaluation. The original
team run passed 79 before the evaluation/relevance tests were added. A later
revision may have more tests. Do not continue after failures merely because some
tests passed. See INTEGRATION_STATUS for the current restricted-session checks.

The script creates `demo-result.json` and `evaluation-semantic.json` in the engine directory. The built-in temporary Git demo is separate from To-do. The evaluation contains four synthetic scenarios; successful execution is not a research accuracy claim.

## 5. Create a separate fresh To-do project

The clone includes an original **JSON-backed** starter at `examples/todo-starter`. Copy it outside the engine repository. Do not copy the already-migrated To-do app from another person's machine.

**Terminal — same PowerShell session:**

```powershell
$appRoot = Join-Path $demoRoot 'testTodoapp'
if (Test-Path -LiteralPath $appRoot) { throw 'testTodoapp already exists. Choose a fresh app folder instead of overwriting it.' }
New-Item -ItemType Directory -Path $appRoot | Out-Null
Get-ChildItem -LiteralPath (Join-Path $engineRoot 'examples\todo-starter') -Force |
    Copy-Item -Destination $appRoot -Recurse
Set-Location $appRoot
git init
git add app.py storage.py index.html test_app.py README.md requirements.txt .gitignore .github/copilot-instructions.md AGENTS.md
git -c user.name='To-do Demo' -c user.email='demo@example.invalid' -c commit.gpgsign=false commit -m 'Create JSON-backed To-do task app'
if ($LASTEXITCODE -ne 0) { throw 'Initial commit failed.' }
git rev-parse HEAD
& $enginePython -m oxmemory init --name testTodoapp --local
if ($LASTEXITCODE -ne 0) { throw 'Memory initialization failed.' }
& $enginePython -m oxmemory status
& $enginePython -m unittest -v
```

Expected: an initial Git commit, project name `testTodoapp`, zero memories, and **five passing app tests**. The per-command Git identity applies only to this demo commit. `--local` configures local extraction defaults; this walkthrough does not call extraction and does not require an extraction server. The init command prints generic next steps mentioning API keys: those keys are not required for this remember/recall flow.

Check your layout:

```text
MemoryLayerDemo/
  installed-packages.txt
  0xMemory/                  engine Git repository
    .venv/                   installed Python dependencies
    START_HERE.md            keep the walkthrough here
    examples/todo-starter/   untouched JSON baseline
  testTodoapp/               separate application Git repository
    .git/
    app.py
    storage.py
    index.html
    test_app.py
    .github/copilot-instructions.md
    .0xmemory/               authoritative memory plus local index
```

The starter excludes `.0xmemory`, `data`, editor configs, and `.env` from Git. App task data and AI memories are different: `data/tasks.json` holds todo items; `.0xmemory/memory/*.md` holds facts and decisions. Do not delete either to simulate a new chat.

## 6. Generate local editor configurations

Run from the engine folder after initializing the app and caching the model:

```powershell
& $enginePython "$engineRoot/scripts/configure-editors.py" --project $appRoot --offline-models --clients vscode codex cursor antigravity
```

The helper merges selected project-local configs and backs up existing files.
Conflicting server entries are refused. Matching entries are left unchanged.
See [editor setup](EDITOR_SETUP.md) and [Codex connection instructions](QUICKSTART_DEMO.md#3-open-the-app-in-your-client).
Keep the app path and engine interpreter separate; never copy Windows configs to Linux.

## 7. Connect your editor

Choose **one** editor now. All subsequent prompts use the same tool names. [EDITOR_SETUP.md](EDITOR_SETUP.md) also contains complete manual JSON templates and links to official configuration references.

### VS Code with GitHub Copilot

Open **testTodoapp itself** using File > Open Folder. Sign in to Copilot, select Agent mode, and run **MCP: List Servers** from Ctrl+Shift+P. Start `0xmemory-todo`, respond to any local-server trust prompt, then enable its tools through Chat's **Configure Tools**. This uses `.vscode/mcp.json`; other chat extensions can have different configuration systems. [Microsoft setup reference](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

### Antigravity

Open **testTodoapp**. Its workspace configuration is `.agents/mcp_config.json`. In Antigravity IDE, use the agent panel's **... > MCP Servers > Manage MCP Servers > View raw config** if you need to inspect or merge configuration, then refresh. Preserve other server entries when merging. Antigravity 2.0 also exposes server management under **Settings > Customizations > Installed MCP Servers**. Use the UI for your installed version; do not assume an old global file path. [Google configuration reference](https://www.antigravity.google/docs/mcp).

### Cursor

Open **testTodoapp**. The project configuration is `.cursor/mcp.json`. Restart Cursor after saving it. Inspect `0xmemory-todo` in the MCP management UI (current documentation calls this **Customize > MCPs**) and enable its tools in Agent chat. Older UI layouts may place MCP under settings. [Cursor configuration reference](https://prod.cursor.com/help/customization/mcp).

### Connection checkpoint — agent prompt

Paste into the editor's agent chat, not PowerShell:

```text
Call the status tool from 0xmemory-todo. Show the project name,
brain path, and memory counts. Do not infer the answer from files.
Stop if the project is not testTodoapp.
```

Expected: project `testTodoapp`, brain `.0xmemory` under this application, zero memories. Expand the tool invocation. An agent saying “connected” without a tool result is not a connection test.

There should be ten tools: `remember`, `recall`, `list`, `forget`, `update`, `status`, `extract`, `observe_commit`, `verify_memory`, `supersede_memory`. Do not call `extract` for this flow; it requires separate LLM provider setup. Tool-use approvals depend on your editor; approve the specific operations you are testing when requested.

## 8. Run and check the application

**Terminal — app directory:**

```powershell
Set-Location $appRoot
& $enginePython -m uvicorn app:app --host 127.0.0.1 --port 8090
```

The terminal stays occupied while the app runs. Open **http://127.0.0.1:8090**. Add `Prepare project review` and `Capture MCP screenshots`; complete one. Refresh and check both tasks and the completion state remain. Stop with Ctrl+C and restart using the same command to check disk persistence.

Use a second terminal for other commands, restoring the variables from section 6 if needed. MCP is launched by the editor; uvicorn launches the web application. They are independent. Do not open an MCP stdio server in a browser.

## 9. Remember the JSON decision

**Agent prompt — Chat A:**

```text
Inspect storage.py and get the full current Git HEAD SHA.

Remember this developer-provided decision using 0xmemory-todo remember:
"We chose JSON file storage for tasks because the assessment lab has no
database service and we want an inspectable prototype."

Save it as type decision, with file_paths ["storage.py"] and commit_sha
set to the full HEAD SHA. Show the saved memory ID and evidence commit.
Do not write the rationale into source files, README, or agent instructions.
```

Wait for the actual remember tool response. Record its ID as **OLD_ID** and the full commit as **INITIAL_SHA** in your test report outside the To-do workspace. The lab rationale is a supplied demo scenario, not an inference from code. Keep this guide outside the agent's opened workspace so recall cannot simply quote it.

If remember fails, do not proceed. File paths must be repository-relative and exist at the evidence commit. Do not manually manufacture memory IDs.

## 10. Recall in a new chat

Click **New Chat** in your editor. Do not attach Chat A, its transcript, or this guide. Keep tools enabled.

**Agent prompt — Chat B:**

```text
Use only the 0xmemory-todo recall tool to tell me:
What task storage did we choose, and why?

Use file_paths ["storage.py"] and include_history false.
Show the memory ID and evidence commit.
Do not read source files, memory files, guides, or previous chats.
```

Pass condition: actual recall invocation returns JSON storage, the lab/inspectable-prototype rationale, OLD_ID, and INITIAL_SHA. Code alone can reveal JSON usage; the saved rationale and tool result distinguish memory retrieval from code inspection. Save the expanded tool call and response.

This demonstrates persistence across agent conversations, not a controlled comparison of model quality. You may restart the editor and repeat this prompt to check server restart persistence too.

## 11. Migrate the app to SQLite

Stop uvicorn with Ctrl+C. Start another agent conversation, **Chat C**.

```text
First use 0xmemory-todo recall to retrieve our task storage decision.

Then migrate testTodoapp from JSON storage to SQLite using Python's
built-in sqlite3. Our new decision is SQLite for atomic task updates
and queryable task data without an external database service.

Requirements:
- Preserve the TaskStore API, existing HTTP endpoints, and UI behavior.
- Store tasks in data/tasks.db.
- Import existing tasks.json once, preserving IDs and completion state.
- Ensure subsequent restarts cannot duplicate or resurrect tasks from JSON.
- Record migration completion even when no JSON file exists initially.
- Add meaningful tests for migration, no resurrection, and persistence.
- Update README with the new storage behavior.

Run tests using ..\0xMemory\.venv\Scripts\python.exe -m unittest -v.
Show changed files and test results.
Do not commit or change any memories yet.
```

The sibling Python path assumes the folder layout above. Agent-generated implementations can differ: assess behavior, not whether they have exactly the same diff or number of tests as the team run. The team reported six passing tests after migration; your agent may add more.

Review the diff. Tests should cover preserved IDs/completion state, persistence after reopening the store, and preventing old JSON from reimporting deleted tasks. Restart the app and check your original browser tasks survived, including the completed one. Delete a task, restart again, and verify it does not return. This is separate from reading test output.

If tests or the browser check fail, have the agent fix the migration before committing. Do not approve a memory statement that the implementation does not support.

## 12. Commit and observe the change

**Agent prompt — same Chat C, after successful review:**

```text
Review the migration diff and commit only the relevant migration source,
tests, and README locally with message "Migrate task storage from JSON to SQLite".
Do not push or commit data files, memory files, or local configuration.
If Git identity is absent, use per-command user.name "To-do Demo" and
user.email "demo@example.invalid" without changing global settings.
Show the full new commit SHA.
Do not change memories yet.
```

Record the full SHA as **NEW_SHA**. Verify the commit includes `storage.py`. If Git asks for signing in your personal setup, resolve that local Git configuration or use a per-command unsigned demo commit. No remote push is needed for the To-do experiment.

Now replace `NEW_SHA` and `OLD_ID` in the following prompt with your real values. Send it separately so the stale state can be captured before replacement.

```text
Call 0xmemory-todo observe_commit with commit NEW_SHA.
Use the MCP list tool to inspect OLD_ID and show its status and observation result.
Then call recall for the task storage decision with file_paths ["storage.py"]
and include_history false. Show whether OLD_ID was returned.
Do not verify, supersede, or create memories yet.
```

Pass condition: OLD_ID is **stale**, affected through `storage.py`, and excluded from ordinary recall. If it is your only memory, there may be no eligible current decision. Other active memories can still be retrieved if you created any.

Observation is an explicit tool call. A Git commit alone does not trigger a watcher. A file change means “needs review,” not “the entire old statement has been proven false.” If observation is skipped, outdated active context can still be returned.

## 13. Review and supersede the old decision

Replace both placeholders with your real values before sending.

**Agent prompt — same chat:**

```text
Inspect storage.py and the tests at commit NEW_SHA.

If the implementation supports the statement below, call
0xmemory-todo supersede_memory with:

id: OLD_ID
content: "testTodoapp now stores tasks in data/tasks.db using SQLite.
We chose SQLite for atomic task updates and queryable task data without
an external database service. Existing JSON tasks are imported once,
preserving IDs and completion state."
commit: NEW_SHA
file_paths: ["storage.py"]
note: Explain the actual code and test evidence you reviewed.

If the evidence does not support this statement, report the mismatch
instead of saving it. Show the replacement memory ID.
Use the list tool to confirm the old memory is superseded and the
replacement is active. Do not delete the old memory.
```

Record the replacement as **NEW_ID**. Pass condition: OLD_ID is superseded, NEW_ID is active, and the old/new entries retain the supersession relationship and evidence. Use `supersede_memory`, not plain `update`, for this replacement demonstration.

If a different experiment changes implementation details while the existing statement remains true, review the code and use `verify_memory` instead. Its fields are `id`, `commit`, and `note`. The application validates evidence paths and commit ordering; your reviewer still has to assess the natural-language claim.

## 14. Recall the current decision in another new chat

Open **New Chat** again. Do not attach the migration conversation.

**Agent prompt — Chat D:**

```text
Use only the 0xmemory-todo recall tool to answer:
What is our current task storage decision, and why?

Use file_paths ["storage.py"] and include_history false.
Show the memory ID and evidence commit.
Do not read source files, memory files, guides, or previous chats.
```

Pass condition: SQLite, its supplied rationale, NEW_ID, and NEW_SHA. OLD_ID must not be returned as current advice. Save the expanded MCP result and answer. The expected fields matter more than the exact wording of the answer.

## 15. Switch editors and inspect history

This is an optional **additional test**, not required to establish the single-editor lifecycle flow. It checks a second MCP client using the same persisted memory.

1. Stop/disable `0xmemory-todo` in the first editor, or close that editor and verify its server has stopped.
2. Open the **same testTodoapp folder** in the second editor. Do not initialize a new brain or copy memories elsewhere.
3. Use the generated configuration for that editor and enable its tools.
4. Call `status` to verify the application and brain path.
5. In a new chat, send the Chat D prompt. Expect the same NEW_ID and NEW_SHA.
6. Record editor/version/model and the real tool result. Repeat for the third editor if desired, stopping the previous server first.

To inspect history, send:

```text
Use 0xmemory-todo recall with include_history true for task storage.
Use list if necessary to show both the original JSON decision and its
SQLite replacement, including IDs, statuses, evidence, and replacement links.
Clearly distinguish historical decisions from the current recommendation.
```

For a visual inspection, stop the editor's memory server and run:

```powershell
& $enginePython -m oxmemory.dashboard --project $appRoot --keyword-only
```

Open **http://127.0.0.1:8765**. Inspect entries and history without creating additional changes. The dashboard's keyword-only option does not exercise semantic retrieval. Stop it with Ctrl+C before restarting the editor MCP server. Browser rendering should be recorded as a separate manual check.

For raw metadata inspection, with the memory server stopped:

```powershell
& $enginePython -m oxmemory memory inspect --project $appRoot
```

## 16. Record results and repeat safely

Copy [TEST_REPORT_TEMPLATE.md](TEST_REPORT_TEMPLATE.md) into your handoff folder outside the To-do workspace. Fill in your versions, engine SHA, IDs, SHAs, expected/actual results, and screenshots. Do not copy the team's existing results and present them as your own run.

Suggested evidence filenames:

```text
01-engine-verification.txt
02-initial-status.png
03-app-json.png
04-remember-old-id.png
05-fresh-chat-json-recall.png
06-migration-tests-and-diff.png
07-observe-stale.png
08-superseded-and-active.png
09-fresh-chat-sqlite-recall.png
10-second-editor-recall.png
```

The team run is documented in [DEMO_RESULTS.md](DEMO_RESULTS.md), with the distinction between user-reported observations and directly executed checks. It does not establish that your environment works.

For another clean run, stop the app/MCP/dashboard processes and create a **new sibling folder**, for example `testTodoapp-run2`, from the JSON starter. Repeat initialization and configuration with `$appRoot` set to that new path. You can keep the logical brain name `testTodoapp`; always record its absolute path. Each run needs its own Git repository, empty brain, configs, and IDs. Keep the completed run intact as evidence; no recursive deletion or Git reset is needed.

## 17. Troubleshooting

| Symptom | Meaning and next action |
| --- | --- |
| Missing starter or lifecycle commands after clone | Wrong or unpublished revision. Obtain the maintainer's published branch/SHA; reinstall editable dependencies if needed. |
| `py` / `git` not recognized | Install the prerequisite, reopen the terminal, and check PATH. Git for Windows may be at `C:\Program Files\Git\cmd\git.exe`; invoke quoted paths with `&`. |
| PowerShell script execution blocked | Use the process-scoped verifier command in section 4. Direct `.venv\Scripts\python.exe` calls do not require activation. |
| `No module named oxmemory` | Wrong Python environment or missing editable installation. Run pip install from engine root using `$enginePython`. |
| `Server` has no `list_tools` | Old server code/dependency mismatch. This revision uses MCP 2.3 request handlers and declares `mcp>=2.3.0,<3`; verify the checked-out revision and reinstall `.[dev]`. |
| Windows WinError 32 during temporary DB cleanup | Ensure current Chroma cleanup fixes and declared version range are installed; stop lingering test/server processes before rerunning. Do not hide teardown errors. |
| Offline model error | First cache the model with offline flags `0` in the same user environment. Then restore flags/restart the editor server. |
| Download timeout / proxy problem | Resolve network or approved proxy access; do not describe keyword fallback as a successful embedding test. |
| Native stdio test fails at pipe creation in a restricted sandbox | Run the full verifier in normal PowerShell. The ordinary-pipe test is supplemental, not permission to claim the native test passed. |
| Server absent in editor | Open the app folder itself; check config location and wrapper (`servers` versus `mcpServers`); use editor logs. |
| Server started but wrong project | Correct the final serve argument, stop/restart the server, and recheck status. |
| Agent answers without a tool call | Enable Agent/tools and explicitly request MCP. Capture expanded invocation; prose alone is not proof. |
| No current result after observation | Expected if the only relevant memory is stale. Review and verify/supersede it. |
| Old entry remains active | Was storage.py linked initially? Was the change committed? Was the new commit observed? Inspect returned evidence and SHA. |
| Supersession rejected | Use the actual ID and a commit that contains the latest observed change and evidence file. Read the reported error before retrying. |
| No browser connection | uvicorn must be running on 8090. MCP start does not launch the app. |
| Port 8090/8765 busy | Stop your previous app/dashboard process or select another port; do not terminate unrelated processes. |
| Incorrect SHA/ID copied from guide | Replace symbolic OLD_ID/NEW_ID/NEW_SHA with values returned in your own run. |
| New chat remembers without MCP | Could be other context; repeat using only recall and inspect its tool response. |

Memory persistence alone is not the research novelty. This example demonstrates explicit code-linked invalidation and reviewed replacement. Automatic contradiction detection, background observation, concurrent writers, and a controlled multi-repository research benchmark are not implemented by these steps.

## 18. macOS and Linux notes

For **Ubuntu**, use [UBUNTU_SETUP.md](UBUNTU_SETUP.md) from the beginning. It
includes prerequisites, Bash verification, generated Linux editor configs, every
lifecycle prompt, and troubleshooting. Do not mix its Bash commands with this
Windows guide.

For **macOS**, the Unix interpreter path is also `.venv/bin/python`, but Ubuntu's
`apt` commands do not apply. Install Git and Python 3.11/3.12 using your macOS
setup, then adapt the Bash workflow and use the portable config generator.
macOS and Ubuntu runtime results have not been established by the Windows tests;
record the actual OS, commands, failures, and editor behavior in the test report.

## 19. Maintainer handoff before a friend clones

For the evaluation and final review package after the application demo, read
[evaluation/README.md](evaluation/README.md),
[evaluation/relevance/README.md](evaluation/relevance/README.md), and
[review-materials/README.md](review-materials/README.md). The experimental relevance
gate is off by default and is not necessary for the lifecycle demonstration.

This documentation was prepared against local working-tree changes. It does not itself publish them. Before distributing a clone URL:

1. Review the engine source, dependency, test, script, documentation, and starter changes together.
2. Include this guide, editor guide, report template, results record, and `examples/todo-starter` in the chosen branch. Include the MCP/lifecycle implementation they depend on.
3. Exclude local `.venv`, `.0xmemory`, `.env`, generated personal configs, and task data.
4. Commit and publish the reviewed branch through your normal repository workflow.
5. Give the tester the clone URL, branch name, and full engine SHA. Have them verify that SHA after checkout.
6. Ask the tester to return their completed report and logs, including failed checks.

No push is performed merely by following the app-demo steps. The starter is distributable through the engine repository; your separate local To-do Git history and memory directory are not required.
