# Local integration status

## 2026-10-28: proactive tool guidance and memory receipts

- Added MCP initialization instructions and explicit tool descriptions for ordinary
  development requests. Added concise `Memory:` receipt guidance using actual
  outcomes and IDs, including empty/irrelevant matches and failures.
- Updated starter agent instructions and the existing demo's local Copilot file.
- Real SDK discovery through the explicit anonymous-pipe diagnostic adapter
  confirmed delivery of initialization guidance and receipt guidance for all ten
  tools. Eight targeted tests passed (six setup tests and two server-creation
  tests), including the starter's five application tests and read-only MCP smoke
  check. The rerun used a fresh workspace-local pytest temp directory and
  `PYTHONUTF8=1` after default temp permissions and console encoding blocked
  initial attempts. No new full-suite or Ubuntu run claimed.
- The developer supplied VS Code screenshots showing automatic storage recall
  invocation and preference save/recall receipts. Both preference entries were
  confirmed on disk. See [evidence and limitations](review-materials/evidence/2026-10-28/README.md).
- Instructions influence agent behavior; they do not enforce calls or control the
  client's UI. Receipts are not independently authenticated tool logs.


## 2026-10-27: one-command To-do setup

- Added Windows `setup-demo.ps1` and Ubuntu `setup-demo.sh`, sharing a Python
  orchestrator. VS Code Copilot and Codex project configs are the defaults.
- Renamed the reusable starter to `examples/todo-starter` and new demo/server
  names to `testTodoapp` / `0xmemory-todo`. Original recorded results and the
  existing sibling testDodoapp are preserved.
- Six setup tests passed, covering config preservation/backups/idempotence,
  conflict preflight, invalid input, existing-project protection, external prompt
  generation, and a real read-only MCP call through the explicit anonymous pipe
  adapter. The integration test also ran all five starter tests successfully.
- Targeted Ruff checks and PowerShell syntax passed. The Windows entry script
  was executed with installed dependencies and cached-model mode. Dependency
  checks passed, but embedding loading failed with Windows Application Control
  WinError 4551 on torch_python.dll. Setup correctly returned failure, saved its
  log/result, and did not create the requested testTodoapp folder.
- No full end-to-end setup PASS is claimed in this session. The first-install
  package download/venv path and the full engine suite were not rerun here.
- Git Bash syntax execution is blocked by its signal-pipe Win32 error 5; Ubuntu
  runtime remains unverified. No operating-system policy was bypassed.
- Installed Codex CLI 0.160.1 was inspected. TOML parses and follows the official
  project configuration schema, but `codex mcp get` did not discover the test
  project's server before an interactive trusted-project session. CLI/Desktop
  tool invocation and VS Code UI validation remain NOT RUN. Follow QUICKSTART_DEMO
  to open/trust the actual app and invoke status; configuration files alone are
  not client integration evidence.


Updated 2026-10-07 after normal-terminal verification and the developer-reported
Copilot Dodo demonstration. Fresh setup: [Windows](START_HERE.md) / [Ubuntu](UBUNTU_SETUP.md).

## Ubuntu documentation and portable setup validation

- Added the complete Ubuntu 24.04 / Python 3.12 walkthrough, with a managed-Python
  alternative, Bash verifier, editor configs, and separate-chat lifecycle test.
- `scripts/configure-editors.py`: Ruff passes. Exercised all three generated
  JSON formats, absolute paths containing spaces, rejection before brain init,
  and rejection of existing configs without mutation.
- A generated config launched the real server and returned the initialized
  project's zero-memory status through the MCP SDK using the existing anonymous
  pipe test adapter on Windows. This is not a Linux/editor UI test.
- The Bash verifier has LF bytes and a Git LF rule. It runs the full test suite
  without deselections, then the demo and semantic evaluation into fresh outputs.
- **Ubuntu runtime and Bash syntax execution are NOT RUN:** WSL returned access
  denied, and Git Bash could not create its signal pipe (Win32 error 5) in this
  restricted session. Do not count these environment failures as verification.
  Run the guide on Ubuntu and record results in TEST_REPORT_TEMPLATE.md.
- Local `.env`, `.venv`, brain, editor configs, and cache directories are not
  tracked Git inputs. A fresh Linux clone recreates them using its own paths.

## Latest relevance and final-materials validation

- Current collection: **89 tests**. The restricted-session run completed with
  **88 passed, 1 explicitly deselected in 147.09 seconds**. Only
  `tests/test_stdio_transport.py::test_stdio_transport` was excluded because the
  native SDK launcher needs Windows pipes unavailable in this sandbox. That test
  remains enabled in verify-local.ps1. The earlier user-run 79-test result below
  is historical and is not relabelled as a current 89-test normal-terminal run.
- Six relevance tests cover cosine math, non-bypass by file hints, fallback,
  empty-context reasons, opt-in configuration, and the fixed data partitions.
- A real MCP SDK/server smoke check enabled the gate through config, rejected an
  unrelated question, and retained the logging answer. Recorded at
  [mcp-smoke.json](evaluation/relevance/mcp-smoke.json).
- Eight development and 16 newly reserved relevance cases ran with real embeddings.
  The selected 0.25 policy did not improve reserved no-answer false positives
  (8/8 for both modes). The gate is disabled by default. See
  [relevance methodology/results](evaluation/relevance/README.md).
- New modules and the presentation generator passed targeted Ruff checks.
  Dataset/policy hashes, Markdown links, HTML slide count, and JavaScript syntax
  were checked. Committed baseline source snapshots match their recorded hashes.
- The 15-slide offline HTML deck is generated. Edge's automatic PDF/visual preview
  failed at Windows IPC creation in the restricted session; no PDF or visual
  inspection is claimed. Print from a normal browser if a PDF is needed.
- Final technical report and demo/viva script are in
  [review-materials](review-materials/README.md). Team/institution formatting and
  independent editor/user replication remain external submission tasks.

## Fixed

- Migrated MCP handlers from the removed v1 decorator API to MCP 2.3 request
  handlers. Updated Tool schema and client response field names to the v2 API.
- Set the supported MCP dependency to `>=2.3.0,<3`.
- Added explicit MemoryStore/VectorStore close operations. Chroma clients release
  their database handles before temporary directory cleanup on Windows.
- Set ChromaDB to `>=1.5.9,<2`, matching the public client close API in the tested version.
- Added cleanup to stdio-server shutdown, HTTP/dashboard lifespan, test fixtures,
  and evaluation runs. Shared clients are closed individually.
- Retained assertions for actual protocol errors, persistence, and real embeddings.

## Verified

Installed versions: MCP 2.3.0, ChromaDB 1.5.9, sentence-transformers 6.1.0,
Python 3.12.0 on Windows.

- **79 tests passed in 66.80 seconds** in the developer's normal Windows
  PowerShell run, followed by the full verifier PASS line. This supersedes the
  earlier restricted-session result of 78 passed / 1 explicitly deselected.
- Models, Markdown, memory lifecycle, MCP handler/resource tests, dashboard API,
  real dashboard HTTP requests, and real embedding persistence checks passed.
- A real MCP SDK ClientSession connected to a real server subprocess through
  ordinary stdin/stdout pipes. It exercised initialization, tool/resource/prompt
  discovery, resource/prompt reads, remember, recall, commit observation,
  supersession, server restart, and fresh-session recall. No server or model
  response was mocked for this transport check.
- `python -m oxmemory.evaluation --semantic --output evaluation-semantic.json`
  completed with the actual embedding model and ChromaDB. The report contains
  four synthetic scenarios across three variants, not a research benchmark.
- `pip check`: no broken requirements. Python compilation, PowerShell syntax,
  and Git whitespace checks passed.

## Environment-specific history and editor validation

The normal SDK `stdio_client` launcher fails inside this restricted session at
Windows `CreateFile` with `PermissionError`, while creating an overlapped named
pipe. This occurs before launching the server. The ordinary-pipe test uses the
same SDK ClientSession and server, with a separate subprocess I/O adapter.

The earlier sandbox command explicitly excluded only
`tests/test_stdio_transport.py::test_stdio_transport`. That test remains enabled
in the normal verification script; no automatic skipping or false PASS was added.
The developer's later normal-terminal run passed this test along with all others.

The developer then reported completing the separate Dodo lifecycle flow through
VS Code Copilot Agent in different chats: remember, recall, commit observation,
stale status, evidence review, supersession, and current-decision recall. Migration
output reported six passing app tests. See [DEMO_RESULTS.md](DEMO_RESULTS.md) for
IDs, commits, evidence provenance, and checks not recorded. Browser acceptance and
Cursor/Antigravity handoffs still need independent recording.

From your regular PowerShell terminal at the MemoryLayer directory, run:

```powershell
$env:PYTHONUTF8 = '1'
powershell -NoProfile -ExecutionPolicy Bypass -File .\0xMemory\scripts\verify-local.ps1 -SkipInstall -OfflineModels
```

This reruns every test, including the native SDK launcher, and the semantic
experiment. `-SkipInstall` uses the dependencies already installed.
`-OfflineModels` uses cached model weights and avoids network retries. The script
stops on any failure and restores the previous model-download environment flags.
For a fresh machine follow START_HERE: cache the model before enabling offline mode.

## Result limits

The new controlled evaluator (`python -m oxmemory.benchmark`) completed five
development and 25 reserved scenarios with real embeddings and Git transitions.
Four new regression tests passed. It changes no production retrieval parameters.
See [evaluation/FINDINGS.md](evaluation/FINDINGS.md) for metric denominators and
the separate pending-review and no-answer failures. The previous 79-test full-run
record predates these four added tests; a current full collection has 83 tests.

The semantic smoke report filters stale memories successfully in its fixtures,
but its no-answer scenario still retrieves unrelated active content. Relevance
thresholds and abstention need further evaluation. These results do not establish
improved coding-task success or general benchmark superiority.

## MCP client configuration

Use [EDITOR_SETUP.md](EDITOR_SETUP.md) for client-specific wrappers and paths.
The example below is a historical local-machine example, not a portable config.

After verification, use an initialized demonstration repository:

```json
{
  "mcpServers": {
    "0xmemory": {
      "command": "C:/Users/moule/Desktop/MemoryLayer/0xMemory/.venv/Scripts/python.exe",
      "args": ["-m", "oxmemory", "serve", "C:/path/to/initialized/demo-repository"]
    }
  }
}
```

Replace the repository path with a Git repository initialized using `0xmemory init`.
The user completed the Copilot connection separately; global editor configuration
was not modified by the setup agent.

## Independent handoff

Handoff checks performed on 2026-10-07:

- Copied the bundled JSON starter into a fresh local test directory, created an
  initial Git commit and empty brain, and passed all five starter tests.
- Parsed all 12 PowerShell command blocks in START_HERE without syntax errors.
- Executed its configuration-generation block verbatim against that fresh app.
- Used each generated config's command/arguments/environment with the real MCP
  SDK and server subprocess: all three discovered ten tools and returned the
  correct project/path with zero memories. This tests the launch definitions,
  not Cursor or Antigravity UI discovery.
- Checked Markdown fences, JSON examples, relative document links, and Git diff
  whitespace. Existing engine tests were not rerun for documentation-only edits;
  their 79-pass result above comes from the developer's earlier full verification.

The engine includes `examples/todo-starter`, an untouched JSON baseline to copy
into a separate Git repository. It contains no saved memories, personal configs,
virtual environment, or SQLite migration. Follow [START_HERE.md](START_HERE.md)
and record new results in [TEST_REPORT_TEMPLATE.md](TEST_REPORT_TEMPLATE.md).
The reviewed engine changes and handoff files must be committed/published before
a remote clone includes them; writing documentation does not publish a branch.
