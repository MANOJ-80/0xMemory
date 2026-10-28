# 0xMemory implementation plan

**Status:** In progress; first evidence-validation slice implemented  
**Design basis:** [`DESIGN_DOCUMENT.md`](DESIGN_DOCUMENT.md), version 0.2  
**Baseline:** Current repository prototype and [`PROJECT_PLAN.md`](PROJECT_PLAN.md)  
**Date:** 28 October 2026

This plan turns the design into a dependency-ordered delivery sequence. It does not imply that the design has been approved or that proposed capabilities are already implemented. Keep the current Markdown store and local Python workflow as the first deployment target; revisit storage and hosting choices only against measured requirements.

## 1. Target for the first research release

Deliver an auditable, local, single-user memory workflow for Python repositories that can:

1. capture small, sourced memory candidates and require review for inferred or sensitive claims;
2. preserve revisions and lifecycle events through correction, supersession, export, and deletion;
3. validate code-linked memories against repository, branch, commit, and working-tree context, and report `supported`, `contradicted`, or `unknown` with reasons;
4. retrieve scoped memories for a coding task, qualify supported answer slots, and abstain when evidence is insufficient;
5. expose the same lifecycle through CLI and MCP, with inspectable health and activity; and
6. demonstrate safety, reliability, retrieval quality, user effort, and downstream coding outcomes on a reproducible multi-session evaluation.

This target does not include hosted multi-user operation, all-language structural indexing, autonomous acceptance of inferred decisions, or a claim of general coding-performance improvement. Those require separate evidence and approval.

## 2. Work already present in the repository

Treat these as baseline capabilities to preserve and measure, not as future work: project-scoped Markdown records with a ChromaDB index; CLI, MCP, and local dashboard interfaces; explicit commit observation; file-level evidence links; manual verify/supersede operations; hybrid lexical/semantic retrieval; an opt-in relevance gate; and synthetic lifecycle/retrieval evaluations. The first implementation slice now also records the branch used when code evidence is reviewed and qualifies linked memories at recall against current HEAD and dirty/untracked paths. This is a conservative change-detection check, not semantic proof. The remaining limits are recorded in `PROJECT_PLAN.md`, `INTEGRATION_STATUS.md`, and `evaluation/`.

Before implementation starts, establish a tagged/reproducible baseline and map each design requirement to existing behavior, partial behavior, or a gap. Do not assume the prototype's synthetic evaluation establishes end-to-end benefit.

## 3. Delivery sequence and exit criteria

| Phase | Priority | Deliverable | Exit criteria | Depends on |
|---|---|---|---|---|
| 0. Scope and policy | Must | Requirement map, threat model, deployment boundary, unresolved decision log, measurable targets | Reviewers agree on first-release memory classes, scopes, capture policy, deletion semantics, branch rules, allowed probes, target clients, and evaluation success criteria | None |
| 1. Durable ledger | Must | Versioned record schema and append-only lifecycle events, migration path, export/restore, integrity checks | Existing Markdown data migrates without provenance loss; interrupted writes recover safely; exports can be re-imported; one-writer/concurrency behavior is explicit and checked | 0 |
| 2. Capture and user control | Must | Candidate inbox, provenance and sensitivity labels, confirmation/rejection, correction, forget/delete | Direct observations and user statements retain source; inferred/decision-like candidates await review; correction preserves history; deletion removes active records, search entries, and declared caches | 0, 1 |
| 3. Repository context and evidence | Must | Repo identity plus branch/HEAD/index/worktree context; resolvable file/symbol/span references; tiered validator | Refactor, semantic change, rename, revert, branch divergence, and uncommitted edits yield correct supported/contradicted/unknown outcomes with reasons; failed checks never appear verified | 0, 1 |
| 4. Retrieval and answerability | Must | Context-aware candidate search, hard scope/state filters, evidence-aware answer slots, explicit abstention, retrieval receipt | No-answer and hard-negative cases are rejected at measured thresholds; returned claims identify evidence and uncertainty; scope filters cannot be bypassed by ranking | 1, 3 |
| 5. Conflict and maintenance | Should | Conflict/review candidates, non-destructive supersession, safe deduplication, expiry/review policy | Competing claims remain inspectable; automation only proposes uncertain merges; lifecycle history remains intact; false conflict and review burden are measured | 1, 2, 3, 4 |
| 6. Integration and user experience | Must | CLI/MCP lifecycle parity, review/inspect UI, diagnostics, integration receipts | Each supported client can capture, recall, inspect, review, correct, and forget; failures and non-use are observable; usability is evaluated with target users | 2, 4, 5 |
| 7. Security and operations | Must | Scope isolation, secret exclusions, safe prompt handling, backup/recovery, degraded mode | Cross-project and user-scope tests pass; retrieved text stays untrusted data; secret/deletion behavior is verified; lexical/manual access works when optional models or Git probes fail | 1–6 |
| 8. Research evaluation and release | Must | Frozen real-history dataset, controlled comparisons, ablations, report, release checklist | Reproducible runs report component and downstream outcomes, denominators, repeated runs, uncertainty, cost, failures, and limits; release claims are supported by results | 0–7 |

**Priority meaning:** Must is required for the declared first research release; Should follows if the phase-0 scope and evaluation justify it. A feature can be deferred only by recording the decision, user impact, and risk in the open-decision log.

## 4. Phase work breakdown

### Phase 0 — Scope and policy

- Define the initial supported memory classes (recommended: project knowledge, task state, and environment/workflow; user preferences only if user-scoped controls are in place).
- Define repository, branch, task, and user scope semantics and inheritance rules.
- Specify auto-accept versus review-required capture classes, sensitivity handling, source retention, and what data can be sent to optional providers.
- Decide active deletion versus tombstone/audit retention, backup retention, export format, and index/cache deletion behavior.
- Define branch/worktree validity and whether probes may execute. Any execution needs explicit policy, bounded time/resources, and a safe environment.
- Set measurable release targets for answerability, stale retrieval, false-stale, capture precision, deletion completeness, latency/cost, and user review effort. Set targets before tuning.
- Deliver a requirement-to-test traceability matrix and record decisions still open from Section 15 of the design.

### Phase 1 — Durable ledger

- Add explicit schema versions and a migration registry for current Markdown records.
- Make lifecycle changes atomic with their event record; define stable IDs and idempotent operations.
- Keep search indexes rebuildable and verify index/store consistency on demand.
- Specify and enforce the initial single-writer strategy; test concurrent reads and safe write contention. Do not claim multi-writer support until it is implemented and evaluated.
- Add backup, restore, export, import, corruption detection, and a documented degraded/read-only path.
- Preserve source references, trust basis, evidence revision, scope, lifecycle state, and prior values across migration.

### Phase 2 — Capture and control

- Represent candidate, accepted, rejected, corrected, and forgotten outcomes with actor, time, reason, provenance, and policy outcome.
- Store concise claims and source pointers rather than raw conversation transcripts by default.
- Require review for model-inferred, ambiguous, sensitive, or decision-like content unless a narrow policy explicitly permits automatic acceptance.
- Provide inspect/list/review/correct/supersede/forget commands and equivalent MCP operations.
- Define deletion across canonical records, lexical/vector indexes, caches, exports, and backup retention. Verify the declared limits rather than promising physical erasure beyond them.
- Add capture-quality labeling and measure unsupported claims and review workload before enabling any unattended extraction path.

### Phase 3 — Repository context and evidence

- Resolve repository identity, branch, HEAD, merge base where relevant, and working-tree/index status for every validation request.
- Expand evidence references from file-level paths to stable symbol/span anchors for Python first; record revision and content hash and handle path renames.
- Implement V0 resolution and V1 conservative hash/semantic checks first. Add deterministic probes only after Phase 0 defines allowed commands and execution limits. Treat model review as optional advice.
- Preserve validation outcomes and reasons as events. An anchor change triggers review; it does not automatically make a claim false.
- Cover branch switches, rebase, revert, missing Git, unavailable parser, and uncommitted modifications with explicit unknown/degraded outcomes.
- Extend to another language only after Python evidence coverage and failure rates meet agreed targets.

### Phase 4 — Retrieval and answerability

- Apply repository/user/branch/lifecycle/privacy filters before candidate ranking.
- Use task/question context, current files/symbols, lexical/semantic matching, evidence freshness, provenance, and measured utility signals for ranking.
- Define answer slots for target question types and return only supported slots. Make missing slots and abstention reasons explicit.
- Keep LLMs off the required hot path; any LLM answerability signal remains advisory until independently calibrated.
- Return bounded context containing claims, states, evidence references, and uncertainty. Use a real tokenizer when available; otherwise label a byte-based budget as an approximation.
- Record a structured retrieval receipt without secret content by default: scope, candidate IDs, outcomes, selected evidence, budget, and tool status.
- Evaluate unanswered and hard-negative queries separately from relevant-answer retrieval; do not enable a gate based solely on a development set.

### Phase 5 — Conflict and maintenance

- Generate possible conflict and near-duplicate candidates using shared entities, answer slots, evidence anchors, scope, and time.
- Require review for high-impact conflicts and uncertain consolidation. A model may propose a relationship but cannot silently resolve it.
- Add explicit expiry/review policies by memory class; decay can affect review priority, not truth state.
- Test supersession, reversion, context-specific exceptions, rejected conflict proposals, and history integrity.
- Measure false conflict rate, missed conflicts, pending-review recall, and reviewer time before automating maintenance.

### Phase 6 — Integration and user experience

- Keep CLI and MCP behavior aligned; publish tool contracts, error states, and compatibility/version policy.
- Provide a human inspection flow for evidence, scope, state, revisions, conflicts, and activity, with search/filter and correction/forget actions.
- Report unavailable providers, failed probes, stale indexes, and client/tool errors visibly. Preserve safe keyword and direct-inspection behavior when optional components are unavailable.
- Measure tool invocation, failure, and receipt accuracy per supported client. Model-facing instructions are not proof that a client invoked a tool.
- Run independent setup and usability sessions using the repository's tester workflow; record browser/editor checks separately from code-level tests.

### Phase 7 — Security and operations

- Test project/user isolation, canonical path handling, excluded files/secrets, malicious repository text, poisoned memories, prompt injection, and safe rendering.
- Ensure recalled content is data, never privileged instructions; bound all content passed to optional models.
- Define local storage/key ownership and encryption expectations for the declared deployment.
- Exercise backup restore, crash recovery, index rebuild, migration rollback or forward recovery, and degraded operation without embeddings, LLM, parser, or Git.
- Establish operational limits for retrieval latency, store size, logging, and sensitive telemetry.
- Close only those deployment risks represented in the declared scope; defer multi-user or hosted requirements explicitly.

### Phase 8 — Research evaluation and release

- Build ordered multi-session tasks on two or three small, real repositories with human-reviewed labels; retain synthetic fixtures for edge cases and label them clearly.
- Include refactors, semantic changes, renames, reverts, uncommitted edits, divergent branches, conflicting sources, missing slots, no-answer queries, capture errors, and adversarial content.
- Freeze repository-level development and held-out partitions before tuning.
- Compare no memory, full-history where feasible, naive memory RAG, current prototype, evidence/JIT validation, and full system under matched model, task, revision, and context budget.
- Ablate commit/evidence validation, answerability gate, file/symbol boosts, and capture review. Count extraction, validation, indexing, retrieval, and review costs.
- Report retrieval/answerability, freshness/conflict, capture/control, client integration, security, and downstream coding outcomes: task/test pass rate, regressions, steps, tokens, latency, repeated errors, convention adherence, and human edits.
- Release only with reproducible instructions, raw results, failures, and claims bounded to tested repositories, clients, languages, and conditions.

## 5. Suggested implementation increments

1. **Increment A — Decide and baseline:** complete Phase 0; freeze prototype revision, dataset snapshots, and current evaluation protocol.
2. **Increment B — Trustworthy lifecycle:** deliver Phases 1–2; migrate existing data and verify correction/deletion/export behavior.
3. **Increment C — Evidence-aware local recall:** deliver Phases 3–4 for Python and one local CLI/MCP workflow; run held-out safety, stale, and no-answer evaluations.
4. **Increment D — Reviewable conflicts and usable controls:** deliver Phases 5–6; complete independent client/user sessions.
5. **Increment E — Research release:** complete Phase 7 and Phase 8; publish the scope, results, costs, limitations, and reproducibility package.

Each increment should end with a reviewable artifact: decision log and traceability matrix; migration/recovery demonstration; evidence and abstention evaluation; client/user study record; then final reproducible report. Do not gate progress on adding a new database or hosted service absent a measured need.

## 6. Cross-cutting definition of done

Every shipped capability in the declared scope must have:

- an explicit owner and documented behavior, inputs, and scope rules;
- an observable success and failure result, including `unknown` where evidence is unavailable;
- a user path to inspect and correct the outcome, and to delete data where applicable;
- tests/evaluation cases for normal behavior, relevant failure modes, and boundary conditions;
- migration, backup, or recovery handling when persistent data is affected; and
- recorded evidence supporting any user-facing or research claim.

A phase is not complete because its code exists. Its exit criteria must be evidenced and its limitations documented.

## 7. Decisions to resolve at the next design review

Use these as the phase-0 agenda; update this list with a decision, owner, and date rather than silently assuming an answer.

| Decision | Recommended starting point | Why it must be explicit |
|---|---|---|
| Research contribution vs product scope | Focus contribution on evidence-aware retrieval, freshness, and abstention; scope other capabilities to a local Python release | Prevents an untestable “complete system” claim |
| Canonical store | Retain Markdown during the first release; benchmark before considering SQLite | Avoids an unsupported migration and keeps records inspectable |
| Capture policy | Explicit user statements/direct observations may be accepted by narrow rules; inferences and decisions require review | Controls unsupported memories |
| Deletion and retention | Remove active data and derived indexes; document tombstone and backup retention | Defines what “forget” means |
| Branch validity | Validate against explicit repo + branch + revision + worktree context; do not generalize across branches by default | Prevents cross-branch misapplication |
| Probe execution | Disabled unless explicitly configured, bounded, and isolated | Repository commands can have side effects |
| Answerability | Deterministic slot coverage and evidence checks first; evaluate any model judge separately | Current relevance results show no-answer remains difficult |
| Supported clients | Select a small set for the first evaluation and report per-client results | Tool guidance does not guarantee invocation |
| Release success | Set numerical thresholds and human-effort ceiling before tuning | Avoids selecting thresholds to fit held-out results |
