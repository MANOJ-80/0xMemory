# 0xMemory

**Recommended: [one-command To-do setup](QUICKSTART_DEMO.md)** for Windows/Ubuntu, VS Code Copilot, and Codex CLI/Desktop. The detailed manual steps below remain available for troubleshooting.

A project-scoped persistent memory layer for AI coding agents, with human-editable
Markdown, a ChromaDB search index, and MCP integration.

The final-year prototype adds **evidence-grounded memory lifecycle management**:
memories link to code evidence, changed files trigger review (not automatic
invalidation), and verified replacement decisions preserve the original history.

**New tester? Choose your operating system:**

| Operating system | Complete clone-to-demo walkthrough |
| --- | --- |
| Windows PowerShell | [START_HERE.md](START_HERE.md) |
| Ubuntu / Bash | [UBUNTU_SETUP.md](UBUNTU_SETUP.md) |

Both guides cover the environment, embeddings, verification, fresh To-do app,
VS Code Copilot / Antigravity / Cursor setup, and the entire memory lifecycle.
Ubuntu runtime validation is still pending; record your independent results.

| Document | Purpose |
| --- | --- |
| [Memory architecture](MEMORY_ARCHITECTURE.md) | How the evidence-grounded design works, its algorithms, boundaries, and comparison with other systems |
| [Complete design](DESIGN_DOCUMENT.md) | Product-level requirements and broader target architecture |
| [Editor setup](EDITOR_SETUP.md) | Manual client configurations |
| [Tester report](TEST_REPORT_TEMPLATE.md) | Record an independent run and evidence |
| [Original demo results](DEMO_RESULTS.md) | Copilot run, IDs, commits, and limits |
| [Integration status](INTEGRATION_STATUS.md) | Verified checks and remaining checks |
| [Project plan](PROJECT_PLAN.md) | Implementation map and research work |
| [Controlled evaluation](evaluation/README.md) | 30 Git-backed synthetic scenarios, reproducible runs, and metrics |
| [Evaluation findings](evaluation/FINDINGS.md) | Measured stale-filtering benefit, review delay, and no-answer failures |
| [Relevance experiment](evaluation/relevance/README.md) | Development-only calibration and the negative reserved result |
| [Final review materials](review-materials/README.md) | Technical report, offline slides, speaker notes, and demo/viva script |

The JSON baseline is in `examples/todo-starter`. Copy it into a separate Git
repository following START_HERE; do not modify the template for your experiment.

## What works

- Store facts, decisions, learnings, preferences, task state, and environment/workflow knowledge in `.0xmemory/memory/`.
- Preserve metadata, code references, confidence, importance, and edit history.
- Suppress exact duplicate memories with matching evidence and tags.
- Search using semantic/keyword fusion and optional file/symbol hints.
- Flag memories for review after an explicit commit inspection; a changed file alone does not mark a claim false.
- Verify or supersede decisions with evidence and a review note.
- Keep review-required memories eligible for qualified recall, exclude superseded memories, and inspect lifecycle history explicitly.
- Integrate through MCP tools, CLI commands, or a local inspection dashboard.
- Extract knowledge through configured local or cloud LLM providers.
- Store project facts, decisions, learnings, preferences, task state, and environment/workflow notes as typed records; task-state entries require a task scope and expire after seven days unless given another expiry.
- Checkpoint long coding tasks with structured progress, blockers, decisions, next steps, validation, and file hints; refreshes preserve earlier snapshots in revision history, and a fresh session can resume with relevant project memories.
- Discover unexpired task checkpoints by matching their objective and open work, so a new session can find a task ID it was not given.
- Stage extracted or uncertain knowledge as review candidates; accepted candidates remain unverified, while rejected candidates are quarantined.
- Keep provenance, trust basis, answer slots, sensitivity, scope, expiry/review dates, and evidence references in each record.
- Capture Python AST symbol anchors alongside file/commit evidence when symbols are supplied; recall checks current branch, committed changes, staged/unstaged edits, renames, and symbol semantic hashes.
- Pass task context, task IDs, and user-scope IDs into recall; scope and sensitivity filters are applied before ranking.
- Return evidence-check states and abstain when requested answer slots are missing; contradicted symbol evidence is not exposed as current advice.
- Inspect possible conflict candidates without automatically resolving them, and inspect a hash-chained activity ledger that stores query hashes rather than raw recall text.
- Inspect a review queue for unreviewed candidates, changed claims, expired memories, and overdue review dates.
- Mark memories as verified only after an explicit evidence review; editing a claim sends it back to review-required state.
- Use structured answer-slot values when answering rationale, owner, date, and location questions, returning only the requested attributes in packed context.
- Refuse new secret-labelled memories, keep sensitive-labelled memories out of ordinary recall, and exclude them from exports unless explicitly requested.
- Import JSON memory backups without overwriting colliding IDs; preserve lifecycle metadata and report skipped, conflicting, or invalid records.
- Record optional helpful/not-helpful feedback as a small ranking signal, separate from evidence trust, and archive task-scoped memories when a task is completed.
- Experiment with an opt-in relevance gate and explicit empty-context reasons.
  The gate is **disabled by default**: it did not improve no-answer retrieval on
  the newly reserved cases. See [the complete result](evaluation/relevance/README.md).

## Install, run, and test

Use Python 3.11 or 3.12. These instructions target the
`architecture/evidence-grounded-memory` branch. The branch must be available in
your clone; it is currently a local working branch until it is published.

### Ubuntu

Install prerequisites (Ubuntu 24.04):

```bash
sudo apt update
sudo apt install -y git python3.12 python3.12-venv
```

From the repository directory, check out the architecture branch if needed,
install the engine, and run the end-to-end setup:

```bash
git switch architecture/evidence-grounded-memory
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
bash scripts/setup-demo.sh --project ../testTodoapp-architecture
```

### Windows PowerShell

Install Git for Windows and Python 3.12. From the repository directory:

```powershell
git switch architecture/evidence-grounded-memory
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-demo.ps1 -Project ..\testTodoapp-architecture
```

The one-command setup reuses `.venv`, checks dependencies and local embeddings,
runs an offline architecture-memory smoke check, creates a fresh To-do app in a
separate Git repository, runs its app tests, writes project-local MCP settings,
and checks MCP tool discovery and project identity. It does not modify or reset
an existing app; choose a new `--project` / `-Project` path for each clean run.
It prints an evidence folder containing logs and a generated `DEMO_FLOW.md` for
the interactive fresh-chat workflow. Sign-in, client trust, and actual agent
tool invocation remain manual steps.

To run the full engine suite and semantic demo/evaluation during setup, add
`--full-verify` on Ubuntu or `-FullVerify` on Windows. This takes longer and
loads the embedding model. The regular setup's focused, deterministic smoke
check needs no model or network; the setup also checks/downloads embeddings.

### Manual install and run

Ubuntu: `python3.12 -m venv .venv`, then use `.venv/bin/python`. Windows:
`py -3.12 -m venv .venv`, then use the venv's `Scripts/python.exe`. On either
OS, install from the repository root with `-m pip install -e '.[dev]'`.

Initialize a target project's brain with the engine venv's Python. For example,
on Ubuntu:

```bash
cd /absolute/path/to/target-project
/absolute/path/to/0xMemory/.venv/bin/python -m oxmemory init
/absolute/path/to/0xMemory/.venv/bin/python -m oxmemory serve "$PWD"
```

On Windows PowerShell, use the same engine Python for both commands:

```powershell
Set-Location C:\path\to\target-project
C:\path\to\0xMemory\.venv\Scripts\python.exe -m oxmemory init
C:\path\to\0xMemory\.venv\Scripts\python.exe -m oxmemory serve (Get-Location).Path
```

The MCP client normally launches `serve` itself. See
[editor setup](EDITOR_SETUP.md) for OS-specific client configuration. Local
embeddings use `all-MiniLM-L6-v2`; its first use downloads model weights. LLM
extraction is optional and can use a configured local or cloud provider.

### How to test the architecture implementation

Run the deterministic architecture smoke check directly from the engine root.
It creates a temporary Git repository and memory brain, then removes them:

```bash
# Ubuntu
.venv/bin/python scripts/smoke_memory_system.py --output memory-smoke.json
```

```powershell
# Windows
& .\.venv\Scripts\python.exe scripts\smoke_memory_system.py --output memory-smoke.json
```

The report lists checks for evidence anchors and evolution, review-required
recall, explicit verification, candidate review, task-scope isolation, answer
slots, sensitive-memory filtering, credential refusal, and the event ledger.
It uses no embedding model or network and does not touch your app repository.

Run the complete Python test suite when you want regression coverage:

```bash
# Ubuntu
.venv/bin/python -m pytest tests/ -v
```

```powershell
# Windows
& .\.venv\Scripts\python.exe -m pytest tests/ -v
```

The full cross-platform verifier also runs the demo and semantic evaluation:
`bash scripts/verify-local.sh` on Ubuntu or
`powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-local.ps1`
on Windows. First-time installs need internet for packages/model weights; use
`--offline-models` / `-OfflineModels` only after the model is cached.

Finally, follow the generated `DEMO_FLOW.md` in a coding-agent client to check
real MCP calls across fresh chats, commit observation, review, and supersession.
Automated smoke success does not prove that an agent client invoked tools or
that memory improved coding-task outcomes.

## Code-aware memory

```sh
0xmemory memory remember "Authentication uses JWT" --file auth.py --commit HEAD
# Change the supporting code and create a commit.
0xmemory memory observe --commit HEAD
0xmemory memory inspect
0xmemory memory supersede OLD_ID "Authentication uses cookie sessions" --note "Reviewed auth.py" --commit HEAD
0xmemory memory recall "How does login work?" --file auth.py
```

A changed file means **needs verification**, not **false**. For Python symbol anchors,
unrelated edits can remain supported when the anchored syntax tree is unchanged. If
the claim still holds, use `0xmemory memory verify ID --note "Reviewed the evidence" --commit HEAD`.
Evidence files must exist at the review commit. The reviewer is responsible for
checking that those files actually support the statement; symbol hashes are evidence
checks, not proof of the natural-language claim.

`memory observe` is an explicit commit inspection, not a background observer or
installed Git hook. Recall checks current branch and changed working-tree paths
just in time, but no continuous observer is installed. Use one writer process per project.

For uncertain knowledge, use `0xmemory memory propose ...`, then
`0xmemory memory review ID --accept --note "..."` after review. Task-scoped records
need a task ID; task-state records expire after seven days by default. Supply that
task ID during recall and call the MCP `complete_task` tool when finished.
For cross-session work, call the MCP `checkpoint_task` tool at a useful milestone
or before ending a session. In a fresh session, use `list_tasks` with a phrase
from the objective or open work, then call `resume_task` with the returned task
ID. Checkpoints capture the objective, completed work, decisions,
blockers, next steps, validation, and relevant files. They are agent-reported
progress, not proof that code or tests are correct. Refreshing a checkpoint
preserves its previous snapshot in the record's revision history.
Use `0xmemory memory activity` to inspect recent memory events, `0xmemory memory find-conflicts`
to generate review candidates, and `0xmemory import --input backup.json` to restore
JSON exports. Import skips sensitive records unless `--include-sensitive` is passed;
secret-labelled and obvious credential-like claims are refused.

## MCP connection

Have your client launch the engine's Python with an explicit target project path.
Replace both example paths with yours:

```json
{
  "mcpServers": {
    "0xmemory": {
      "command": "/absolute/path/to/0xMemory/.venv/bin/python",
      "args": ["-m", "oxmemory", "serve", "/absolute/path/to/target-project"],
      "env": { "PYTHONUTF8": "1" }
    }
  }
}
```

On Windows use `.venv/Scripts/python.exe`. This wrapper is for Cursor/Antigravity;
VS Code uses `servers` and `type: "stdio"`. See [EDITOR_SETUP.md](EDITOR_SETUP.md).
The client launches stdio; no browser URL or separate server terminal is required.

Tools include `remember`, `recall`, `checkpoint_task`, `list_tasks`, `resume_task`, `complete_task`,
`list`, `update`, `forget`, `extract`, `status`, `observe_commit`, `review_queue`,
`verify_memory`, and `supersede_memory`. Whether tools are called
automatically depends on the connected agent's behavior and instructions.

The server sends proactive memory-workflow guidance during MCP initialization,
and tool descriptions explain when to recall, remember, and observe commits.
The starter's agent instruction files reinforce this for ordinary requests such
as "Why did we choose this storage design?" Users need not name tools in every
prompt. These are model-facing instructions, not enforced hooks: verify actual
tool activity before claiming automatic invocation. After updating the engine,
restart its MCP connection and start a fresh chat so the client can reload the
guidance. Memory writes should capture durable approved decisions or verified
learnings, not every conversation message.

The guidance also asks the assistant to append one compact receipt to its answer,
such as `Memory: recalled mem-abc123; saved mem-def456`. It must use actual tool
outcomes and IDs, distinguish existing entries from new saves, and report failures
or no relevant match honestly. No receipt is requested when no memory tool ran in
the turn. This is assistant-rendered guidance, not a server-controlled UI element
or an independent audit log; clients may not always follow it.

## Demo, dashboard, evaluation

```sh
python -m oxmemory.demo --output demo-result.json
python -m oxmemory.dashboard --project /path/to/project --keyword-only
python -m oxmemory.evaluation --output evaluation-smoke.json
python -m oxmemory.benchmark --semantic --output evaluation/my-run
```

Open the dashboard at `http://127.0.0.1:8765`. The demo creates a temporary Git
repository and exercises a JWT-to-cookie migration across fresh memory sessions.

The default evaluation uses four synthetic scenarios and keyword-only retrieval.
It checks the pipeline; it is not a research benchmark. Add `--semantic` to run
real embeddings. The bounded context uses UTF-8 bytes as a conservative token-budget
proxy; actual model tokens and coding-task success are not yet measured.

The separate `benchmark` command adds 30 fixed synthetic scenarios with real Git
transitions and a controlled lifecycle-filtering ablation. Use a new output folder
for each run. See [methodology](evaluation/README.md) and [findings](evaluation/FINDINGS.md).
Its reserved partition showed no outdated retrieval after filtering, but lost
still-valid context pending review and did not solve no-answer relevance. This is
not a measurement of autonomous coding performance.

## Storage

| Path | Purpose |
| --- | --- |
| `.0xmemory/brain.md` | Manually maintained project overview |
| `.0xmemory/memory/*.md` | Authoritative memories and lifecycle metadata |
| `.0xmemory/sessions/` | Saved session records |
| `.0xmemory/.store/` | Rebuildable local vector index |

Old Markdown remains readable. After manually editing memories, run
`0xmemory rebuild` to refresh the index. Preserve metadata comments when editing;
removing them also removes evidence and lifecycle state.

## Tests

```sh
pytest tests/ -v
python -m unittest discover -s tests -p test_lifecycle.py -v
python -m unittest discover -s tests -p test_dashboard_evaluation.py -v
```

Near-duplicate consolidation (beyond candidate suggestions), automatic conflict
classification, symbol indexing beyond manually supplied Python anchors, background
observation, transactional multi-writer storage, cross-project user memory, and a real multi-repository research
evaluation remain open work. The current changes have not yet been evaluated as a
complete implementation or measured for downstream coding-task gains.
