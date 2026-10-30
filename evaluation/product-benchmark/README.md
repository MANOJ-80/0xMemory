# GEDAM product benchmark (new protocol)

This benchmark asks whether GEDAM improves multi-session coding work, what its
retrieval and memory-write behavior contributes, and how many tokens, calls, and
seconds those benefits cost. It is a new protocol. It does not reuse scores,
labels, scenarios, or conclusions from earlier project evaluations.

## Current pilot implementation

The exploratory pilot and raw artifacts are in [`pilot/`](pilot/), with
human-readable results in [`RESULTS.md`](RESULTS.md). Reproduce the local
synthetic retrieval checks and paired Codex coding pilot from the repository
root with:

```bash
PYTHONPATH=src .venv/bin/python evaluation/product-benchmark/run_retrieval_pilot.py
PYTHONPATH=src .venv/bin/python evaluation/product-benchmark/run_pilot.py
```

The coding runner uses the locally authenticated Codex CLI, pins
`gpt-6-luna`, runs two randomized-order pairs per task family, and retains
prompts, agent event logs, turn-usage JSON, test logs, and result rows under
`evaluation/product-benchmark/pilot/`. It manually seeds synthetic setup facts;
it does not benchmark extraction or memory writing. It is a small feasibility
pilot, not the confirmatory protocol described below.

## Study question and estimand

For a fixed coding agent, model snapshot, repository task, and setup-session
experience, what is the paired change in successful completion of a later,
fresh-session coding task when the GEDAM product is enabled? The primary
estimand is the difference in task success probability between GEDAM and
no-persistent-memory runs over the held-out task families.

The unit of generalization is the **task family** (a repository plus setup and
follow-up scenario). Repeated agent runs are repeated measurements within a
family; they are not additional independent task families.

## Conditions

Use three arms, with the first two as the primary product comparison:

1. **No persistent memory:** start the same setup session, then start a fresh
   follow-up session with the same checkout. Do not retain or inject project
   memory across sessions.
2. **GEDAM:** use the product's normal capture/write path in the setup session;
   start a fresh follow-up session and allow normal Git-aware retrieval and
   context packing.
3. **Token-matched irrelevant-context control:** use the no-memory path, but
   inject a length-matched unrelated project note. This is a secondary
   diagnostic that distinguishes useful memory from a generic extra-context
   effect. It must not contain the answer or misleading instructions.

If the research claim is specifically about GEDAM's Git-aware trust layer,
add a fourth *diagnostic* arm: same memory records and retrieval budget with
Git evidence/lifecycle/answerability checks disabled. Keep it secondary; the
product-level claim remains GEDAM versus no persistent memory.

## Task suite

Build a private, versioned set of real repositories and paired setup/follow-up
tasks. Each setup session teaches or records knowledge that cannot be inferred
from the final checkout alone. Examples include an architectural decision,
approved convention, previous failed fix, branch-specific constraint, or
dependency migration. The follow-up asks for a realistic issue fix or change.
Every task family contains a frozen repository revision, setup transcript or
script, expected memory facts, follow-up prompt, hidden tests, safety checks,
and a scoring rubric.

Stratify before data collection across:

- Memory usefulness: directly useful, distractor-only, and no-answer/control.
- Repository scale and language; include more than one independent repository
  family.
- Claim state: current and supported, superseded/stale, branch-specific,
  historical, conflicting, and insufficiently evidenced.
- Work type: bug fix, feature, refactor, test repair, and operational change.
- Context pressure: small, medium, and near the configured context-window limit.

Use human-authored or carefully transformed tasks and keep held-out prompts,
tests, and labels private until scoring. Two reviewers independently validate
answerability, expected facts, test validity, and prohibited actions; resolve
disagreements before unblinding. Exclude tasks that can be completed from the
visible checkout alone if their purpose is to test cross-session memory.

## Controlled run procedure

For each task family and repetition, create fresh isolated copies of repository,
GEDAM store, agent conversation, and logs. Pin the exact agent harness and model
snapshot, sampling settings, tool definitions and permissions, context window,
runtime image, dependencies, network policy, and timeout. Run the same setup
experience in each condition; only the persistent-memory treatment differs.
Randomize condition order within task and repetition, and use a published seed.
Do not reuse conversations, worktrees, caches, or GEDAM state across arms.

Before each run, capture the exact user prompt, system/developer prompt hashes,
tool schema hashes, visible repository state, GEDAM state, and rendered context.
Check that no arm label appears in model-visible content. Audit control
filesystem state and tool traces to detect GEDAM leakage. Keep the evaluator and
hidden tests inaccessible to the agent. Run hidden tests after the agent stops;
never let the agent read their outputs and continue editing.

Use three repetitions per task family for an initial feasibility pilot. Use
pilot variance and a preregistered minimum worthwhile improvement to calculate
the main study size. A credible first confirmatory study should target at least
100 independent task families and five paired repetitions, across several
repository families. More repetitions do not substitute for more task families.

## Outcomes

### Primary

- **Follow-up task success:** binary, decided before the study. Success requires
  all required hidden tests to pass, no critical regression, and no prohibited
  action. Report numerator, denominator, timeout/API-failure policy, and
  missing-run counts.

### Quality and memory behavior

- Hidden test pass fraction and test-category outcomes.
- Blinded patch rubric: functional correctness, regression risk, maintainability,
  scope adherence, and use of the intended prior-session knowledge.
- Memory fact recall: relevant fact retrieved, correct fact used, and answer
  supported by current evidence.
- Stale/unsupported-memory use rate; valid-memory suppression rate; conflict and
  no-answer false-answer rate.
- Safety violations by severity, including secret disclosure, destructive
  commands, out-of-scope edits, and policy violations.
- First-attempt success and number of repair cycles.

### Retrieval and suppression metrics

Score retrieval against gold memory labels created and reviewed before model
runs. Keep retrieval quality separate from downstream coding success. Report
macro averages across eligible queries, raw numerators/denominators, and
category-specific results. A query with no relevant stored memory is excluded
from recall and valid-memory-suppression denominators, but included in
no-answer/abstention measures.

| Metric | Definition | Denominator / interpretation |
| --- | --- | --- |
| Recall@k | Relevant gold memory IDs in the top k divided by all relevant gold IDs for the query. | Answerable queries with at least one relevant stored memory; macro average. |
| MRR | Reciprocal rank of the first relevant memory; zero when none is returned. | Same answerable query set as Recall@k. |
| Precision@k | Relevant returned IDs divided by returned IDs up to k. | Queries with at least one returned item; also report empty-return rate. |
| Correct abstention rate | Correctly abstained no-answer queries divided by no-answer queries. | No-answer queries, including unrelated, missing, and unresolved evidence cases. |
| False-answer rate | No-answer queries where the system returned an unsupported answer or memory as current. | No-answer queries; distinguish retrieval output from agent-generated claims. |
| Stale-hit rate | Queries returning a gold-labeled stale/contradicted memory in the context. | Queries where a stale candidate is available; report stale hit IDs too. |
| Valid-memory suppression rate | Queries where a relevant, still-valid gold memory was available but omitted/withheld. | Queries with a valid relevant memory; report pending-review and evidence-uncertain cases separately. |
| Conflict handling accuracy | Correctly surfaced conflict or abstention on labeled contradictory current claims. | Queries with a gold-labeled unresolved conflict. |
| Supported-answer rate | Completed answers whose material claims are supported by retrieved, current evidence. | Completed answers with a blinded evidence review. |
| Context budget compliance | Runs whose packed GEDAM context stays within the configured budget divided by runs with a budget. | All GEDAM retrieval runs. |
| Useful context density | Number of gold-relevant facts included divided by packed context tokens, scaled per 1,000 tokens. | Queries with token accounting; pair with recall to avoid rewarding tiny but incomplete contexts. |
| Redundant context fraction | Estimated tokens in semantically duplicate/repeated context divided by total packed-context tokens. | Runs with non-empty packed context; label the duplicate adjudication method. |

Define stale truth labels independently of GEDAM lifecycle status. A memory
marked review-required is not automatically false; if it remains factually
valid, its omission counts as valid-memory suppression and its pending-review
category remains visible. Report stale-hit and suppression side by side so a
precision gain cannot hide loss of useful memory.

### Efficiency and context pressure

- Total reported input, cached input, cache-write input, output, and reasoning
  tokens across setup and follow-up sessions, where surfaced by the provider.
- Input/output tokens per API request or agent turn, preserving the source
  granularity; report total and per-successful-task totals.
- Model/API request and tool-call counts, retries, elapsed agent runtime,
  retrieval latency, memory-write latency, and local memory storage size.
- Peak context utilization per turn: provider-reported input tokens divided by
  the pinned context limit; peak, mean, and turns above 80%, 90%, and 95%.
- Retrieval-context tokens/bytes, prompt bytes, and tokenizer-based estimates
  when provider usage is missing. Label estimates separately from reported
  usage and record tokenizer name/version.
- Context utilization: packed-memory tokens / retrieval budget and, separately,
  provider-reported full input tokens / configured model context window. These
  are different denominators; label them distinctly in tables and charts.
- All-in GEDAM overhead: include the setup session, memory extraction/write,
  retrieval, and follow-up usage. Also show follow-up-only results to explain
  amortization, but never present those as the all-in cost.

## Token and cost accounting

Retain one raw usage record per provider response or agent-reported turn, with
condition, task family, repetition, session, model identifier, timestamp,
request/turn ID where available, input, cached-input, cache-write, output,
reasoning-output, and provider-reported cost fields. Include failed calls and
retries. Preserve the raw event stream or a redacted immutable copy with each
run artifact. A missing field is `null`, never zero.

Use these labels in all reports:

- **Provider-reported:** token/cost numbers emitted by the configured API or
  agent harness. State whether totals are request-level or turn-level. For
  Codex CLI, the adapter records `turn.completed.usage` values verbatim; these
  are Codex-reported turn totals, not a claim of per-HTTP-request billing data.
- **Derived from provider report:** uncached input is `input - cached input -
  cache-write input` only when those fields are documented as non-overlapping
  subsets by that provider. Otherwise report the components without deriving
  uncached usage.
- **Estimated:** tokenizer or byte-based counts, inferred context utilization,
  and list-price calculations. Include method and version. Do not combine these
  with provider-reported totals in one unlabeled field.

Provider-reported usage is exact as reported for that source and granularity;
it may not equal invoice billing after subscription terms, discounts, retries,
or later adjustments. For a cost estimate, freeze the price sheet and date,
separate uncached input, cached input, cache writes, and output rates, and state
that it is an estimate. If agent subscription usage does not expose a monetary
cost, report tokens and runtime; do not infer a dollar amount.

The benchmark runner's context selection estimate is not the agent's total
prompt usage. The latter also includes system instructions, tool definitions,
repository reads, prior turns, and hidden harness context. Compare treatment
arms using provider-reported input totals when available, and always show
coverage (`runs with usage / eligible runs`).

## Analysis plan

Preregister the primary outcome, exclusions, task strata, success rubric,
sample-size target, and analysis before opening held-out results. Estimate the
paired GEDAM-minus-control change in success rate with task family and
repository clustering. Use a paired binary analysis or mixed-effects logistic
model; report absolute risk difference, relative effect, 95% confidence
interval, and raw counts. Include a sensitivity analysis at the repository
level. For tokens, cost, and runtime, report paired differences and ratios with
cluster-aware confidence intervals; include medians and quantiles because
usage is typically skewed. Control false discovery across secondary endpoints
or label those analyses exploratory.

Publish every assigned run, including failures, timeouts, and usage gaps. Blind
patch graders to condition and randomize patch order. Report inter-rater
agreement. Do not claim improved correctness from retrieval metrics alone, or
claim lower cost from smaller retrieved context alone.

## Paper and presentation outputs

Use one main outcome table and one token/context table; keep retrieval and
downstream coding claims visibly separate. Fill the following from the frozen
run artifacts only. Report `n/N` beside every percentage, and use `N/A` when a
denominator is empty. Do not replace missing usage with zero.

| Condition | Task success (n/N) | Hidden test pass | Recall@k | Stale-hit rate | Valid-memory suppression | Correct abstention | Mean provider input tokens | Mean cached input tokens | Mean output tokens | Mean peak context utilization | Median runtime |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| No persistent memory | TBD | TBD | N/A | N/A | N/A | N/A | TBD | TBD | TBD | TBD | TBD |
| GEDAM | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Token-matched unrelated context | TBD | TBD | N/A | N/A | N/A | N/A | TBD | TBD | TBD | TBD | TBD |

Suggested main figure: paired task-success difference with 95% confidence
interval, grouped by memory-usefulness and repository family. Suggested second
figure: token cost versus task success per task family, with points showing
repetitions and GEDAM retrieval context distinguished from full model input.
Suggested retrieval figure: stale-hit rate against valid-memory suppression;
annotate denominators and show no-answer abstention separately. These visual
specifications are templates, not measured results.

## Codex CLI usage adapter

`codex_usage_adapter.py` invokes Codex CLI for one run, writes the agent's
visible prompt from a file, and collects each JSONL `turn.completed.usage`
record. It emits summed Codex-reported turn usage plus the individual records
to the requested usage JSON. Preserve the separate Codex stdout/stderr log from
the caller. Pin `--model` explicitly for study runs; record `codex --version`
and all CLI configuration. The adapter does not turn estimated tokens into
provider-exact usage or establish benchmark outcomes by itself.

Example command shape for a runner that provides placeholders:

```json
[
  "python3", "evaluation/product-benchmark/codex_usage_adapter.py",
  "--repo", "{repo}", "--prompt-file", "{prompt_file}",
  "--usage-file", "{usage_file}", "--model", "PINNED_MODEL_ID"
]
```

This adapter needs Codex CLI authentication and its normal local state. A
separate benchmark invocation should record the CLI's effective model and
configuration; do not write credentials into manifests or result artifacts.

## Required run artifacts

Every run directory should be immutable and contain: protocol and suite
version, frozen task manifest and hashes, randomization seed, environment and
model/harness versions, prompt/tool hashes, GEDAM configuration, all run-level
outcomes, usage records with coverage, hidden-test results, blinded grading
records, analysis code and output, exclusions, and a concise report. Store
private tests and unreleased tasks separately from artifacts intended for
publication.
