# EDAM implementation plan and status

## Plan

1. Preserve Markdown as the canonical store, ChromaDB as a rebuildable index,
   and existing CLI/MCP/Git interfaces.
2. Add task analysis and query planning for current, historical, approval,
   architectural, and symbol questions; extract dates, paths, technologies,
   symbols, and answer slots.
3. Combine semantic and exact keyword/identifier retrieval with bounded
   read-only code-definition and reference search. Keep code evidence distinct
   from memory claims.
4. Link memories to files, symbols, commits, provenance, verification state,
   extraction confidence, claim-truth confidence, and explicit claim-validity
   periods.
5. Resolve lifecycle and temporal state, separate overlapping conflicts from
   historical state, and surface unresolved/missing repository evidence.
6. Score relevance, evidence, temporal fit, freshness, scope, provenance,
   utility, and both confidence signals. Abstain when candidates conflict or
   fail evidence/relevance/answerability requirements.
7. Build a low-redundancy context within a shared estimated-token budget and
   report token estimate, UTF-8 bytes, omissions, and reason diagnostics.
8. Expose the behavior and claim metadata through storage, CLI, MCP, and
   dashboard flows; retain a selectable baseline policy.
9. Compare no-memory, basic retrieval, current 0xMemory, and EDAM on identical
   relevance and Git-lifecycle fixtures. Include evidence, abstention, ranking,
   latency, and budget ablations/metrics.
10. Provide controlled coding-task trials that use identical tasks, repository
    revisions, memory sets, agent commands, and tests across the four retrieval
    conditions; record task success, test pass, latency, context size, diffs,
    and model usage when reported by the agent.

## Runtime implementation

The existing working tree now implements items 1–8. Set
`retrieval.architecture` to `baseline` for RRF-oriented ranking or `edam` for
configured EDAM scoring. Markdown records remain compatible; optional fields
have defaults, so there is no bulk migration.

The task analyzer is deterministic and inspectable in recall output. It finds
explicit dates, source paths, common technologies, exact symbols, intent, and
answer slots. Retrieval combines keyword ranking, semantic ranking, and file
and symbol hints. Code search is a bounded read-only scan: Python uses AST;
JavaScript, TypeScript, Go, Rust, Java, and C# use conservative declaration
patterns. Exact identifier references are included and attached to definition
results. Source snippets are labeled untrusted and remain separate from
memories.

Evidence includes file/symbol anchors, Git commit, branch, and content hashes.
Changed files trigger review rather than automatic invalidation. Anchors that
remain semantically unchanged can continue to be supported; unresolvable or
deleted evidence is distinguished from changed-but-uncertain evidence. Human
verification and supersession remain explicit lifecycle operations.

Structured claims accept `claim_subject`, `claim_predicate`, `claim_value`, and
optional `claim_environment`, `claim_confidence`, `valid_from`, and `valid_to`.
Claim validity uses half-open intervals `[valid_from, valid_to)`. It is distinct
from `valid_until`, which retains its existing record-expiry behavior. Current
queries filter out claims outside their validity period and abstain on
overlapping contradictory claims. Historical queries preserve superseded
records and avoid treating non-overlapping historical values as conflicts.
Free-form claims are not automatically converted into structured triples.
`claim_state` separately records `asserted`, `proposed`, `evaluating`,
`adopted`, `rejected`, or `unknown`; current implementation retrieval excludes
non-adopted options, while explicit approval/history queries can inspect them.
Changing state requires a note and creates a revision and audit event. The
state is exposed through storage, CLI, MCP, and dashboard controls.

Historical conversation lookup is a separate read-only source. It runs only
for explicit historical queries, ranks user/assistant messages by lexical
overlap, excludes tool output and obvious credentials, labels results as
untrusted historical evidence, and charges them to the same context budget.
Conversation snippets never become memory claims automatically.

Ranking uses separate claim-truth and extraction-confidence signals, along
with evidence state, provenance, temporal fit, freshness, scope, utility, and
relevance. Review-required memories remain eligible with a penalty. Conflicts,
missing answer slots, temporal exclusions, evidence state, and budget decisions
are returned as diagnostics.

Context packing greedily selects high-value, less-redundant records. The shared
budget covers memory and code evidence. When no model tokenizer is configured,
the returned token estimate is `ceil(UTF-8 bytes / 3)`; the exact UTF-8 byte
count is also returned. This estimate is intentionally conservative and is not
a model-specific token count.

The four-condition commit-lifecycle evaluator and relevance/ablation evaluator
are implemented. `0xmemory-coding-eval` adds paired agent coding tasks and test
execution from a JSON manifest. It isolates each run in a temporary repository
copy and records logs, test outcomes, task checks, context cost, retrieval and
agent latency, diffs, and optional model usage.

## Remaining validation

The evaluator infrastructure is implemented; the full proposed empirical study
is not. The current checked-in datasets are synthetic and assistant-authored.
No independent multi-repository labels, human-reviewed coding tasks, or actual
four-condition coding-agent run were supplied or executed. Use the manifest
format in `evaluation/README.md` to run that study before making claims about
coding success or general accuracy. Keep development threshold calibration
separate from held-out evaluation.

The code index is not a persistent language-server index or a complete
cross-reference graph. Its language parsers are conservative. The system does
not semantically prove that source code entails a natural-language claim; it
reports anchor continuity and lexical value comparisons as evidence signals.

## Verification performed

- 80 tests passed across lifecycle, retrieval, benchmark, models, Markdown, and
  memory-store modules.
- Python compilation and `git diff --check` passed.
- The held-out keyword/file-proxy lifecycle run completed 27 scenarios and 128
  variant-checkpoints. EDAM answerable recall/MRR was 0.65 versus 0.95 for
  `current`; outdated-hit rate was 0.167 versus 0.583; valid-memory suppression
  was 0.35 versus 0.05; no-answer false-positive rate was 0.333 versus 0.75.
  This shows a substantial recall trade-off and is not an overall win claim.
- The run uses no vector embeddings. MCP integration could not be collected
  because the environment lacks the `mcp` package; installing it failed because
  package-index DNS/network access is unavailable. Dashboard integration tests
  also require unavailable FastAPI and the live HTTP test is blocked by the
  sandbox's socket restriction. These integrations compile, but were not
  runtime-verified here.

The checked-in datasets are synthetic and assistant-authored. No independent
multi-repository labels, human-reviewed coding tasks, or actual coding-agent
comparison were run. Keep development threshold calibration separate from
held-out evaluation before tuning the observed recall trade-off.
