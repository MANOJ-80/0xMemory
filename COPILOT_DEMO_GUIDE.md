# Demonstrate 0xMemory with VS Code Copilot and testDodoapp

> This is the original machine-specific walkthrough. For a friend starting from
> a clone, use [START_HERE.md](START_HERE.md) to create a fresh JSON starter and
> generate their paths. The original Dodo app has now completed its SQLite
> migration: reopening it will not show zero memories or the JSON baseline.
> See [DEMO_RESULTS.md](DEMO_RESULTS.md) for the recorded run.

This walkthrough uses a separate application to demonstrate persistent decisions across fresh Copilot chats, followed by a code change that invalidates an old decision. The application starts with JSON storage. Copilot will implement the SQLite migration during your demonstration.

## 1. What is already prepared

```text
C:\Users\moule\Desktop\MemoryLayer\
  0xMemory\                 Memory engine and existing Python environment
  testDodoapp\              Separate Git repository and runnable todo app
    app.py                  FastAPI endpoints
    storage.py              JSON task persistence
    index.html              Browser interface
    test_app.py             Five API/persistence tests
    .vscode\mcp.json        Copilot MCP configuration
    .github\copilot-instructions.md
    .0xmemory\              This application's own memory store
```

The initial app commit is `ba7baeb`. All five starter tests passed. An actual MCP client initialized the server using the prepared configuration, found ten tools, and received `project_name: testDodoapp` with zero memories. The VS Code UI connection still needs the steps below.

The Python executable belongs to **0xMemory**, while the final server argument points to **testDodoapp**. This lets another project use the engine without mixing its memories with the engine's own memories.

## 2. Open the correct folder

In VS Code, use **File > Open Folder** and select:

```text
C:\Users\moule\Desktop\MemoryLayer\testDodoapp
```

Open this folder alone for the demonstration, rather than its parent or the 0xMemory source folder. Sign in to GitHub Copilot and select **Agent** in Chat.

## 3. MCP configuration

The following file is already saved as `testDodoapp/.vscode/mcp.json`:

```json
{
  "servers": {
    "0xmemory-dodo": {
      "type": "stdio",
      "command": "C:/Users/moule/Desktop/MemoryLayer/0xMemory/.venv/Scripts/python.exe",
      "args": ["-m", "oxmemory", "serve", "C:/Users/moule/Desktop/MemoryLayer/testDodoapp"],
      "env": {
        "PYTHONUTF8": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1"
      }
    }
  }
}
```

VS Code launches this subprocess and communicates through standard input/output. There is no MCP port to enter and no separate server terminal to keep open. The offline flags use your already-cached embedding model. Remember/recall do not require an OpenAI key or Ollama; Copilot itself still uses your Copilot account. The optional `extract` tool is outside this demo and has separate LLM requirements.

Press **Ctrl+Shift+P**, run **MCP: List Servers**, select **0xmemory-dodo**, and start it. Review/accept the trust prompt for this local server if shown. In Chat, use **Configure Tools** and enable its tools. UI wording can vary by VS Code version. See Microsoft's [server setup](https://code.visualstudio.com/docs/agent-customization/mcp-servers) and [configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration).

Expected tools: `remember`, `recall`, `list`, `forget`, `update`, `status`, `extract`, `observe_commit`, `verify_memory`, `supersede_memory`.

Send this first prompt to Copilot:

```text
Call the status tool from 0xmemory-dodo. Show the project name, brain path,
and memory counts. Do not infer these from files. Stop if this is not testDodoapp.
```

Expect `testDodoapp`, a brain path ending in `testDodoapp\.0xmemory`, and zero memories before your first remember operation. Expand the tool invocation to confirm Copilot actually called MCP.

## 4. Run the application

In VS Code's PowerShell terminal:

```powershell
Set-Location C:\Users\moule\Desktop\MemoryLayer\testDodoapp
..\0xMemory\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8090
```

Open **http://127.0.0.1:8090**. Add two tasks, complete one, and refresh. Tasks should remain. The app writes `data/tasks.json`; that file is ignored by Git. Stop the app with **Ctrl+C** when needed.

In a second terminal, run the starter tests:

```powershell
Set-Location C:\Users\moule\Desktop\MemoryLayer\testDodoapp
..\0xMemory\.venv\Scripts\python.exe -m unittest -v
```

Expected: five passing tests. The app and MCP are independent processes: app port 8090 is unrelated to the stdio connection.

## 5. Chat A: store a decision

Use this scenario rationale for the demonstration. It is a developer-provided decision, not something the model should invent from the code.

```text
Inspect storage.py and get the full current Git HEAD SHA.

Our decision for this demo is: testDodoapp currently persists tasks in
data/tasks.json. We chose JSON for the first review because the assessment
lab has no database service and we want an inspectable prototype.

Use 0xmemory-dodo remember to save this as a decision, with file_paths
["storage.py"] and commit_sha set to the full HEAD SHA. Show the returned
memory ID and evidence commit. Do not copy the decision into source files,
README, or Copilot instructions.
```

Record the returned ID as `OLD_ID`. Keep the actual ID, not this placeholder. The rationale is deliberately absent from the app's source and instructions. This guide is outside the Dodo workspace for the same reason.

## 6. Chat B: prove recall in a fresh chat

Use **New Chat**. Do not paste the previous conversation or decision.

```text
Use only 0xmemory-dodo recall to explain what task storage approach we chose
and why. Query for the task persistence decision and use file_paths
["storage.py"]. Return the memory ID and evidence commit. Do not read
.0xmemory files, setup guides, or previous chats to answer.
```

Expected: JSON storage, the lab/prototype rationale, and `OLD_ID`. Save a screenshot of the expanded MCP invocation and response. An answer that merely mentions JSON is insufficient: Copilot could discover that from source. The rationale and actual tool result are the useful evidence.

You can repeat this in a fresh chat with another Copilot model if available. Using one Copilot client demonstrates session persistence; a second model extends the demonstration but does not establish support for every AI client.

## 7. Chat C: implement a real change

Stop the running app before migration. In a new Agent chat:

```text
First recall our task storage decision through 0xmemory-dodo.

Now migrate task persistence from JSON to SQLite using Python's built-in
sqlite3. Our new rationale is atomic task updates and queryable task data
while still requiring no external database service.

Preserve the TaskStore API, HTTP endpoints, and UI behavior. Use
data/tasks.db. Import existing tasks.json on first migration without losing
IDs or completion state. Make import idempotent so subsequent restarts
cannot duplicate or resurrect tasks from the old JSON file.

Add meaningful migration/restart tests and run the full unittest suite
using ..\0xMemory\.venv\Scripts\python.exe. Update README to describe the
new storage. Show the diff and test results. Leave memory lifecycle changes
for my next prompt.
```

Review the changes. Restart the app with the same uvicorn command and verify the two original tasks and completion state survived. Create another task and restart once more to check persistence. These are acceptance criteria, not results already claimed by this guide.

Then send:

```text
Commit the reviewed SQLite migration and its tests locally. Stage only
the relevant source, tests, and README changes. Do not commit data files,
.0xmemory, or local configuration. Do not push. Show the full new commit SHA.
If Git has no identity configured, use per-command user.name "Dodo Demo"
and user.email "demo@example.invalid"; do not change global Git settings.
```

If Git is unavailable on PATH, its executable on this computer is `C:\Program Files\Git\cmd\git.exe`. Record the resulting commit as `NEW_SHA`.

## 8. Observe the change, then review the decision

Replace the placeholders below with your actual ID and SHA:

```text
Call 0xmemory-dodo observe_commit with commit NEW_SHA.
Use its list tool to inspect OLD_ID and show its status. Then call recall
for the task storage decision with include_history false. Do not yet
verify, replace, or create any memories.
```

Expected: the linked JSON decision becomes **stale** because `storage.py` changed. Normal recall must exclude that old entry. Other unrelated active memories, if you added any, may still appear.

Observation is explicit in this prototype. Editing a file alone does not automatically mark memory stale, and a changed file is not proof that every associated statement is false.

Now perform evidence review and replacement:

```text
Inspect storage.py and the migration commit NEW_SHA. Check whether the
old JSON storage decision OLD_ID has been replaced by the implementation.
If the evidence supports it, call 0xmemory-dodo supersede_memory with:
- id: OLD_ID
- content: testDodoapp now persists tasks in data/tasks.db using SQLite.
  We chose SQLite for atomic task updates and queryable task data without
  requiring an external database service. Existing JSON tasks are imported
  once without losing IDs or completion state.
- commit: NEW_SHA
- file_paths: ["storage.py"]
- note: explain the actual code and test evidence you reviewed.
Show the returned replacement ID. If any part of this statement is not
supported, report the mismatch instead of recording it as verified.
```

Expected: old entry **superseded**, replacement entry **active**, history and links preserved. Record the replacement as `NEW_ID`. If a memory remains true despite a file edit, use `verify_memory` after review instead; here the storage decision actually changed.

## 9. Chat D: retrieve the current decision

Start another **New Chat**:

```text
Using only 0xmemory-dodo recall, tell me the current task storage decision
and rationale. Use file_paths ["storage.py"] and include_history false.
Show the memory ID and evidence commit. Do not read memory files or guides.
```

Expected: SQLite, the new rationale, `NEW_ID`, and `NEW_SHA`. The old JSON decision must not appear as current advice.

Then ask:

```text
Use recall with include_history true, and list if needed, to show the old
and new task storage decisions, their statuses, and supersession links.
Clearly distinguish history from the current recommendation.
```

The `.0xmemory` files can now also be opened for inspection after the tool-based retrieval has been demonstrated. Keep them between chats and app restarts.

## 10. Troubleshooting

| Symptom | Check |
| --- | --- |
| Server absent | Open testDodoapp itself; verify `.vscode/mcp.json` exists there. |
| Server fails to start | Use MCP: List Servers and inspect its output. Verify the absolute Python path. |
| Wrong project in status | The final `args` entry must be testDodoapp, not the 0xMemory engine folder. |
| Copilot answers without tools | Select Agent mode, enable tools in Configure Tools, and explicitly request the named tool. |
| No tools after configuration changes | Restart the server; use MCP: Reset Cached Tools if necessary. |
| Offline embedding model error | The flags require an existing cached model. Your verification already passed real embeddings; check that this config uses the same Python executable/user. |
| Git is not recognized | Use `& 'C:\Program Files\Git\cmd\git.exe'` in PowerShell. |
| CLI Unicode error in a manual terminal | Set `$env:PYTHONUTF8='1'` before the Python command; MCP config already sets it. |
| Old decision still active | Ensure the code was committed, evidence includes storage.py, and observe_commit processed the new commit. |
| Recall has no current decision after observation | Expected until evidence review verifies or supersedes the stale entry. |
| Browser cannot connect | Start uvicorn and open port 8090. Starting MCP does not start the app. |

Do not manually run `serve` and expect a browser page: stdio waits for protocol messages from its client. Avoid simultaneous memory mutations from multiple editor/server instances during the demo.

## 11. Evidence for your project review

Capture: the running app; successful tests; status showing the separate project; remember with OLD_ID; fresh-chat recall with rationale; migration diff and commit; stale status after observation; superseded/active history; and fresh-chat recall with NEW_ID.

This demonstrates project isolation, persistent session memory, code-linked invalidation, reviewed replacement, and preservation of decision history. It is a functional case study, not a measurement of retrieval accuracy or proof of improved coding performance. Those require a separately designed evaluation.
