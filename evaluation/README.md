# Commit-aware retrieval experiment

## Controlled coding-task trials

The four-condition coding runner is available as `0xmemory-coding-eval`. It
uses a fixed repository revision, task, and memory fixture for each of
`no_memory`, `basic_retrieval`, `current_0xmemory`, and `edam`. Each trial runs
in its own temporary clone that preserves the repository history. The same agent command and test command
are used for all conditions; the prompt file contains the retrieved context.

Manifest example:

```json
{
  "agent_model": "record the exact model and settings here",
  "agent_command": ["my-agent", "--repo", "{repo}", "--prompt-file", "{prompt_file}", "--usage-json", "{usage_file}"],
  "timeout_seconds": 1800,
  "tasks": [
    {
      "id": "repo-auth-migration",
      "repository": "../repositories/service-a",
      "revision": "0123456789abcdef",
      "query": "Why did we adopt cookie sessions?",
      "objective": "Add session renewal while preserving the documented auth design.",
      "test_command": ["python", "-m", "pytest", "-q"],
      "memories": [
        {
          "id": "auth-decision",
          "type": "decision",
          "content": "Authentication uses cookie sessions because ...",
          "file_paths": ["src/auth/service.py"],
          "symbols": ["authenticate_user"],
          "claim_subject": "authentication",
          "claim_predicate": "uses",
          "claim_value": "cookie sessions",
          "claim_confidence": 0.9
        }
      ]
    }
  ]
}
```

Run with `0xmemory-coding-eval --manifest tasks.json --output run-001`; add
`--semantic` to use the configured embedding backend. The agent may write a JSON
usage report to `{usage_file}` with `calls`, `input_tokens`, and
`output_tokens`. Results include test and task success, estimated context size,
retrieval latency, agent runtime, diffs, logs, and optional reported model usage.
Provide multiple repository histories and independently reviewed tasks in the
manifest for a multi-repository study. The runner is infrastructure; it does not
create independent labels or establish an EDAM advantage by itself.

For Ubuntu installation and Bash reproduction commands, follow [Ubuntu setup](../UBUNTU_SETUP.md#14-optional-editor-handoff-dashboard-and-evaluation). Record Linux results separately from the committed Windows artifacts.

This directory contains a reproducible **synthetic functional evaluation**, not
an independently validated research benchmark. It tests the retrieval consequences
of real Git observation and explicitly supplied review actions. It does not run
Copilot or measure generated code quality.

The checked-in results are a frozen two-condition evaluation of an earlier
retrieval implementation. The current runner has four conditions and records
budgeted recall; rerun it into a new output directory to evaluate the current
working tree. Do not rewrite the historical result artifacts to resemble a
rerun.

## Read these artifacts

- [Development report](development/REPORT.md): five scenarios used for checking
  the harness before running the reserved partition.
- [Reserved-partition report](held-out/REPORT.md): 25 additional scenarios.
- [Interpretation](FINDINGS.md): result denominators, tradeoffs, and report wording.
- `development/scenarios.json` and `held-out/scenarios.json`: the historical
  30-case dataset and labels from the frozen evaluation. A current run snapshots
  the expanded 34-case dataset in its own output directory.
- `results.json` in each run: per-query retrieval, lifecycle audit, actual Git
  commits/diffs, package versions, source fingerprints, and metrics.
- `summary.csv` in each run: aggregates and each metric's sample count.
- `source/`: exact evaluator and dataset-generator snapshots matching the recorded
  source hashes. The first-run sources precede subsequent formatting and
  output-serialization cleanup; the dataset and retrieval logic are unchanged.
- `charts/*.svg`: offline, standalone descriptive bar charts. Each bar spans
  0–100%; these are not statistical plots with confidence intervals.

## Dataset and split

| Category | Development | Reserved | Total | Evaluation point |
| --- | ---: | ---: | ---: | --- |
| Decision becomes outdated | 1 | 7 | 8 | After observation, before replacement |
| Unrelated file changes | 1 | 5 | 6 | After observation |
| Linked file changes, claim remains true | 1 | 5 | 6 | Pending review and after verification |
| Reviewed decision is replaced | 1 | 5 | 6 | After supersession |
| No stored answer | 1 | 3 | 4 | After an unrelated commit |
| Supporting evidence deleted | 1 | 1 | 2 | After deletion is observed |
| Changed evidence remains ambiguous | 1 | 1 | 2 | After ambiguous change is observed |
| Total | 7 | 27 | 34 | 40 checkpoints, 160 current variant results |

All scenarios were authored and partitioned before executing the semantic runs.
The first case in each category is development. The remaining 25 cases were not
used to choose ranking parameters or a relevance threshold. This is a reserved
synthetic partition: the same assistant authored all cases and labels, so it is
not blinded or independent. Human review of the labels is still needed before
presenting this as a research dataset. No production ranking parameters were tuned
against either partition in this experiment.

Each scenario has one evidence-linked decision and six unrelated active memories.
Replacement adds an eighth memory. Python configuration files represent small
policy changes, not full production repositories. Queries and file hints are
authored fixtures; no-answer queries deliberately have no evidence-file hint.

## Controlled comparison

The current runner uses production `rank_memories` with the same query, corpus,
file hints, hybrid retrieval, semantic candidate order, and k across four
conditions:

- **no_memory:** returns no persistent memories.
- **basic:** `include_history=True`; lifecycle filtering is disabled.
- **current:** baseline ranking with lifecycle filtering enabled.
- **edam:** EDAM relevance gate, evidence-aware scoring, abstention, and adaptive
  context packing.

The basic/current pair isolates lifecycle filtering; EDAM adds its retrieval
policy. Production ranks are computed over eligible candidates, so filtering
can change the ranks of remaining memories.

All memory conditions receive the same actual Chroma semantic query result. The runner
performs indexing and semantic queries outside the production fallback handler,
checks corpus coverage, and stops on failure. A semantic run therefore cannot
silently become a keyword-only run. It loads the real all-MiniLM-L6-v2 model once
and shares it across isolated repositories.

The runner initializes temporary Git repositories, creates real Git transitions,
validates evidence files, calls `observe_commit`, then `verify` or `supersede`
where the fixture requires a reviewed transition. Status is never preassigned to
stale/superseded to manufacture the outcome. Initial fixture memories use stable
IDs to avoid random UUID tie-breaking. Replacement IDs are generated by the real
lifecycle operation and recorded in the audit.

Reviews are fixture-provided statements after known code changes. This evaluates
review recording and retrieval behavior, not whether an AI can independently
determine that a natural-language claim is true.

## Metric definitions

| Metric | Definition and denominator |
| --- | --- |
| Recall@5 | Relevant retrieved IDs / relevant stored IDs, averaged only over checkpoints with a stored true answer. |
| MRR | Reciprocal of the rank of the first relevant result; zero if missing; only answerable checkpoints. |
| Outdated hit rate | Fraction of checkpoints containing a factually outdated fixture memory where that memory appears in the top five. |
| Outdated fraction | Outdated IDs / returned IDs for each query, then macro average; empty results contribute zero. |
| Ineligible hit rate | Fraction of checkpoints with stale/superseded entries where any such entry is returned. A stale entry can still be factually true. |
| No-answer false positive | Fraction of checkpoints without a relevant stored answer where any content is returned. This is not a claim that an LLM hallucinated. |
| Update correctness | On supersession cases, replacement is retrieved AND the old outdated entry is absent. |

Truth labels are independent of lifecycle status. A still-valid memory remains
labelled relevant while awaiting verification. This makes its temporary loss
visible rather than defining the enhanced system's output as correct by construction.

Changed-but-unreviewed scenarios have no stored current answer: the replacement
exists in code but was not yet saved as memory. Their no-answer failures are
reported alongside, and separately by category from, unrelated-question cases.

The six valid-refactor scenarios each contribute two correlated checkpoints.
Do not describe 36 checkpoints as 36 independent scenarios. Raw JSON exposes
checkpoint names so pending and completed review can be analyzed separately.

## Reproduce on Windows

From the engine repository after the setup in [START_HERE](../START_HERE.md):

```powershell
$env:PYTHONUTF8='1'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.\.venv\Scripts\python.exe -m pytest tests/test_benchmark.py -v
.\.venv\Scripts\python.exe -m oxmemory.benchmark --partition development --semantic --output evaluation/reproduction-development
.\.venv\Scripts\python.exe -m oxmemory.benchmark --partition held_out --semantic --output evaluation/reproduction-held-out
```

Use the offline flags only after caching the model. For macOS/Linux use
`.venv/bin/python` and shell-appropriate environment variables. The output folder
must not already exist; the runner refuses to overwrite a previous experiment.
Choose a new output name on every repeat. A failed run may leave only a frozen
dataset; a complete run must have results, CSV, report, and charts.

For a fast Git/keyword check without embedding packages:

```powershell
.\.venv\Scripts\python.exe -m oxmemory.benchmark --partition development --output evaluation/keyword-check
```

That output is explicitly labelled `keyword_file_proxy` and is not interchangeable
with semantic results. The original four-case `oxmemory.evaluation` smoke module
remains available but does not isolate lifecycle filtering in the same way.

Check dataset SHA-256 matches across partitions/reproductions. Record package
versions and engine revision; the first run records its dirty working-tree state
because the new evaluator had not yet been committed. Do not compare raw fusion
scores as calibrated probabilities. Timing is deliberately not reported as a
performance comparison; model caching and sequential execution would confound it.

The frozen dataset file uses canonical UTF-8/LF bytes, so its raw file hash matches
the reported digest on Windows too. Source snapshots use their original bytes.

## Next experiment, after preserving this result

The no-answer cases expose a relevance/abstention gap. Any threshold or relevance
gate must be developed on development cases, then evaluated against newly reserved
cases because these results have now been inspected. Preserve this run unchanged.
Add larger corpora, more distractors, multiple relevant entries, real repository
changes, human-labelled questions, and model coding tasks before generalizing.
