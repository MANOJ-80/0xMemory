# Final-year implementation plan

## Research question

Does repository-evidence-grounded, task-aware memory reduce stale or irrelevant
context and improve multi-session coding performance compared with no-memory,
basic semantic-memory, and temporal-graph baselines?

Mem0 and Zep/Graphiti already provide capable general-purpose memory, hybrid
retrieval, graph/temporal features, and source provenance. The coding-specific
hypothesis is narrower: making Git revisions and code anchors first-class evidence,
separating task checkpoints from durable project knowledge, and validating claims
against the current checkout may better support evolving repositories. That advantage
is not established until tested with matched tasks, models, context budgets, and data.

Keep Markdown and ChromaDB for the prototype. Update the review's technology slide
to match this implementation rather than introducing PostgreSQL solely to match a slide.

## Implemented first milestone

- Backward-compatible Markdown metadata for evidence, confidence, importance,
  timestamps, links, states, and revision history.
- Safe entry replacement/deletion and vector upserts when content changes.
- Exact duplicate suppression for the same normalized content, tags, and evidence.
- Active, stale (needs verification), and superseded states.
- Repository-relative file and optional symbol links, with commit references.
- Explicit commit inspection that marks affected memories stale. Replaying an old
  commit cannot invalidate evidence established later. Subsequent changes to already
  stale evidence advance its review requirement.
- Explicit verification and replacement with notes. Evidence paths must exist at
  the review commit; that commit must include the latest known evidence change.
- Hybrid reciprocal-rank fusion of semantic and lexical candidates, with file and
  symbol boosts; stale/history entries are excluded by default.
- Separate query and task-context retrieval channels, with a lower task-context
  contribution and answerability support based on the current question.
- Structured task checkpoints with revision history, expiry, and fresh-session
  discovery and resume retrieval.
- Python syntax-aware evidence hashes for caller-supplied symbol anchors.
- A bounded context string with evidence and retrieval explanations.
- CLI and MCP lifecycle operations, local inspection dashboard, synthetic evaluation.

## Run the demo

From the `0xMemory` directory, using Python 3.11 or 3.12:

```sh
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -e ".[dev]"
python -m oxmemory.demo --output demo-result.json
python -m oxmemory.evaluation --output evaluation-smoke.json
```

The demo makes two commits in a temporary repository. It remembers JWT, changes
the code to cookie sessions, marks the old decision stale, records an explicit
review and replacement, and starts a new store instance that retrieves only the
current decision. It never commits changes in your real project.

The default demo and evaluation do not need a running LLM or embedding model.
`--semantic` on the evaluation enables real ChromaDB/embedding retrieval and fails
visibly if those dependencies or model weights are unavailable.

## Try the workflow on a demonstration repository

Run from that repository's Git root, after its first commit:

```sh
0xmemory init
0xmemory memory remember "Authentication uses JWT" --file auth.py --commit HEAD
# Record the returned ID, then edit auth.py and commit the migration.
0xmemory memory observe --commit HEAD
0xmemory memory inspect
0xmemory memory supersede OLD_ID "Authentication uses cookie sessions" --commit HEAD --note "Checked AUTH_METHOD in auth.py"
0xmemory memory recall "How does authentication work?" --file auth.py
0xmemory memory recall "authentication" --history
```

If a file changed but the decision remains valid, use:

```sh
0xmemory memory verify MEMORY_ID --commit HEAD --note "Reviewed the refactor; authentication still uses JWT"
```

For renamed or replacement evidence, pass `--file NEW_PATH` to `supersede`.
The old decision keeps its original evidence and replacement link.

MCP clients get `observe_commit`, `verify_memory`, and `supersede_memory` in
addition to the existing tools. `remember` accepts `file_paths`, `symbols`, and
`commit_sha`. `recall` accepts file/symbol hints, `include_history`, and `token_budget`.
The MCP response's `context.context` field is the bounded context string.

## Inspect in the browser

```sh
python -m oxmemory.dashboard --project /path/to/demo-repository --keyword-only
```

Open `http://127.0.0.1:8765`. Browse lifecycle states and revision histories,
search with an optional file hint, inspect the latest commit, and record reviews.
Remove `--keyword-only` when embeddings are installed. Read the actual code before
confirming a memory: the dashboard validates file existence and commit order,
not the truth of a natural-language statement.

## Validation performed in this workspace

The new standard-library test suites cover storage regression cases, real Git
transitions, evidence validation, hybrid fusion using a mocked vector backend,
bounded context, dashboard ASGI requests, and evaluation metrics.

```sh
python -m unittest discover -s tests -p test_lifecycle.py -v
python -m unittest discover -s tests -p test_dashboard_evaluation.py -v
python -m compileall -q src tests
```

The developer's normal Windows PowerShell verification passed all 79 tests,
including native MCP stdio and real embeddings, followed by the demo and semantic
evaluation. This supersedes the earlier sandbox run of 78 tests with one native
pipe-launcher check deselected due to environment permissions.

The developer then reported the Dodo JSON-to-SQLite lifecycle flow through VS Code
Copilot in fresh chats. See [DEMO_RESULTS.md](DEMO_RESULTS.md) for the record and
its limits, and [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md) for integration
details. Browser acceptance and additional editor handoffs need independent
recording. New testers should follow [START_HERE.md](START_HERE.md).

```sh
pytest tests/ -v
ruff check src/
python -m oxmemory.evaluation --semantic --output evaluation-semantic.json
```

## Limits of this milestone

- Commit observation is explicit. There is no automatic post-commit hook or
  continuous watcher; recall checks repository state just in time.
- Code links and symbols are supplied by the caller; Python AST hashes check
  supplied anchors, but the system does not automatically index every repository
  symbol or support equivalent anchors across languages.
- Review notes are human/agent assertions after inspection, not semantic proofs.
- Exact duplicate suppression is implemented; near-duplicate consolidation and
  automatic contradiction classification remain future work. Confidence and
  importance are distinct, but confidence is not calibrated.
- Metadata writes are atomic per file. Use one writer process per project;
  concurrent processes and cross-file transactions are not supported.
- Retrieval reads the Markdown corpus and currently overfetches vector candidates
  to filter against authoritative lifecycle states. Benchmark before scaling it.
- `token_budget` uses UTF-8 byte length as a conservative context-size proxy.
  It does not measure model tokens. Metadata in the surrounding JSON response is
  outside that context-string budget. Add a model tokenizer before token claims.
- Existing unlinked memories cannot be invalidated using file changes.
- Old Markdown cannot recover metadata that previous versions never saved.
- The 30-case synthetic retrieval experiment measures lifecycle behavior, not
  model-generated answers or coding-task success. New retrieval and checkpoint
  algorithms require a fresh evaluation run.

## Remaining project phases

A subsequent 24-case relevance experiment selected a cosine cutoff on eight
development questions and tested it unchanged on 16 new reserved questions. It
retained all eight valid test answers but returned content for all eight unanswered
test questions. The gate is implemented, opt-in, and disabled by default; no-answer
retrieval is still unresolved. See [the result](evaluation/relevance/README.md).
The technical report, 15-slide offline presentation, and demo/viva script are in
[review-materials](review-materials/README.md). Institution-specific names and
formatting still need to be filled in before academic submission.

The first controlled synthetic evaluation is now implemented and executed:
30 Git-backed scenarios, five development and 25 reserved, using identical hybrid
retrieval with lifecycle filtering enabled/disabled. Results include raw evidence,
CSV summaries, reports, and charts. See [evaluation/FINDINGS.md](evaluation/FINDINGS.md).
This is an initial synthetic study; human label review and a real-repository dataset
remain open. The no-answer and pending-review limitations are explicitly measured.

1. **Independent reproduction:** publish the reviewed engine/starter revision and
   have a teammate follow START_HERE on a fresh environment. Record browser checks
   and Cursor/Antigravity handoffs. Consider an opt-in observer hook after the
   explicit workflow is reproduced reliably.
2. **Code structure:** index Python functions/classes, track renames, and attach
   evidence spans; extend to other languages only after the Python path works.
3. **Memory management:** generate near-duplicate/conflict review candidates;
   consolidate only supported claims while retaining provenance. Add extraction
   quality tests before allowing unattended updates.
4. **Research dataset:** extend beyond the initial 30 synthetic fixtures to
   human-reviewed multi-session scenarios across
   two or three small repositories. Include changed facts, unrelated changes,
   reverts, renames, conflicting sources, and no-answer cases. Label synthetic
   examples and keep development/tuning scenarios separate from evaluation.
5. **Controlled experiment:** compare no memory, a basic semantic baseline,
   evidence-grounded 0xMemory, and direct Mem0/Zep or faithful documented baselines
   where their setup permits, using the same model, tasks, context budget, and
   repository revisions. Add ablations for evidence validation, task-context fusion,
   task checkpoints, and file/symbol boosts. Measure Recall@k, MRR, stale retrieval,
   answerability, checkpoint resumption, coding tests passed, model tokens, user
   review burden, and repeated-run latency including extraction/update costs.
6. **Report:** record raw results and failures; do not claim novelty for persistence
   alone or universal superiority. Present the specific algorithm, constraints,
   ablations, and observed results.

Suggested team split: memory/storage, code-awareness/retrieval, and evaluation/UI.
The next review can show the Dodo migration and decision history, followed by
independent reproduction results, before discussing benchmark improvements. The
temporary authentication migration remains useful as an automated smoke demo.
