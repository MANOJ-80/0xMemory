# 0xMemory

**Recommended: [one-command To-do setup](QUICKSTART_DEMO.md)** for Windows/Ubuntu, VS Code Copilot, and Codex CLI/Desktop. The detailed manual steps below remain available for troubleshooting.

A project-scoped persistent memory layer for AI coding agents, with human-editable
Markdown, a ChromaDB search index, and MCP integration.

The final-year prototype adds **commit-aware memory lifecycle management**:
memories link to code evidence, changed files trigger verification, and replacement
decisions preserve the original history.

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

- Store facts, decisions, learnings, and preferences in `.0xmemory/memory/`.
- Preserve metadata, code references, confidence, importance, and edit history.
- Suppress exact duplicate memories with matching evidence and tags.
- Search using semantic/keyword fusion and optional file/symbol hints.
- Mark memories stale after an explicit commit inspection.
- Verify or supersede decisions with evidence and a review note.
- Exclude stale/superseded memories from normal recall; inspect history explicitly.
- Integrate through MCP tools, CLI commands, or a local inspection dashboard.
- Extract knowledge through configured local or cloud LLM providers.
- Experiment with an opt-in relevance gate and explicit empty-context reasons.
  The gate is **disabled by default**: it did not improve no-answer retrieval on
  the newly reserved cases. See [the complete result](evaluation/relevance/README.md).

## Install the repository version

Use Python 3.11 or 3.12:

```sh
python -m venv .venv
# Activate the environment using your shell's activation command.
python -m pip install -e ".[dev]"
```

From the root of a project you want to remember:

```sh
0xmemory init
0xmemory serve
```

Local embeddings use `all-MiniLM-L6-v2`; the first load may download model weights.
LLM extraction can use local providers or configured cloud providers. Choose local
providers explicitly when keeping extraction data on-device is required.

## Code-aware memory

```sh
0xmemory memory remember "Authentication uses JWT" --file auth.py --commit HEAD
# Change the supporting code and create a commit.
0xmemory memory observe --commit HEAD
0xmemory memory inspect
0xmemory memory supersede OLD_ID "Authentication uses cookie sessions" --note "Reviewed auth.py" --commit HEAD
0xmemory memory recall "How does login work?" --file auth.py
```

A changed file means **needs verification**, not **false**. If the fact still holds,
use `0xmemory memory verify ID --note "Reviewed the evidence" --commit HEAD`.
Evidence files must exist at the review commit. The reviewer is responsible for
checking that those files actually support the statement.

`memory observe` is an explicit command, not a background observer or installed
Git hook. Uncommitted edits are not monitored. Use one writer process per project.

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

Tools include `remember`, `recall`, `list`, `update`, `forget`, `extract`, `status`,
`observe_commit`, `verify_memory`, and `supersede_memory`. Whether tools are called
automatically depends on the connected agent's behavior and instructions.

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

Near-duplicate consolidation, automatic conflict classification, code parsing,
background observation, and a real multi-repository research evaluation remain
planned work. See [PROJECT_PLAN.md](PROJECT_PLAN.md).
