# Local integration status

Updated 2026-10-07 after normal-terminal verification and the developer-reported
Copilot Dodo demonstration. Fresh setup: [START_HERE.md](START_HERE.md).

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

The engine includes `examples/dodo-starter`, an untouched JSON baseline to copy
into a separate Git repository. It contains no saved memories, personal configs,
virtual environment, or SQLite migration. Follow [START_HERE.md](START_HERE.md)
and record new results in [TEST_REPORT_TEMPLATE.md](TEST_REPORT_TEMPLATE.md).
The reviewed engine changes and handoff files must be committed/published before
a remote clone includes them; writing documentation does not publish a branch.
