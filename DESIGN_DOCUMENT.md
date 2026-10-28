# 0xMemory — Design for a Complete Memory System for AI Coding Agents

**Status:** Working design, not an implementation commitment  
**Version:** 0.2  
**Date:** 28 October 2026

This document defines the intended end-to-end problem and a design direction for 0xMemory. It builds on the supplied *0xMemory v2 — Design Document: Evidence-Grounded Memory with Tiered Validation for AI Coding Agents* and the current repository prototype. It is a design artifact only: the architecture, phases, and policies below are proposals until reviewed and prioritized.

## 1. Summary

0xMemory should help coding agents carry useful knowledge across sessions while a repository, task, and team evolve. It should capture information with provenance, retrieve only relevant and answerable memories, explain the evidence and uncertainty, detect possible staleness, preserve change history, and let people correct or remove stored information. Its value must be measured by downstream coding outcomes and operating cost, not by recall scores alone.

The system is a local-first, project-aware memory service with:

1. **A typed memory ledger** for project knowledge, task state, reusable experience, and user preferences.
2. **A capture pipeline** that records candidate memories with source, confidence, scope, and review status.
3. **A repository evidence layer** that associates code-related claims with symbols, spans, commits, and working-tree state.
4. **A retrieval and answerability pipeline** that uses task context, code context, and memory evidence, and abstains when no candidate answers the question.
5. **A validation and conflict workflow** that tracks uncertainty and competing versions without silently deleting history.
6. **Agent and user interfaces** for recall, capture, review, correction, deletion, and audit.
7. **A privacy, security, and reliability envelope** for local data, multiple clients, failures, migrations, and recovery.
8. **An evaluation program** connecting memory behavior to multi-session coding performance, user burden, and cost.

The goal is a complete design, not a promise that every capability ships at once. Each capability must have an explicit owner, policy, and evaluation criterion before it is claimed as implemented.

## 2. Problem statement

Coding agents repeatedly lose useful context between sessions and may retrieve context that is irrelevant, incomplete, unsafe, or no longer true. The repository may change independently of the memory system. Agent clients differ in how reliably they call tools. Users also need to understand, correct, and delete what the system remembers.

The system must address these failures:

| ID | Failure | Example |
|---|---|---|
| F1 | Amnesia | A new session cannot explain why a storage choice was made. |
| F2 | Staleness | A remembered implementation claim conflicts with the current branch. |
| F3 | False staleness | A harmless refactor hides a still-valid decision. |
| F4 | Irrelevant recall | A related fact is returned even though it does not answer the question. |
| F5 | Missing detail | A memory answers what technology is used but not who approved it, yet the agent implies it knows. |
| F6 | Capture error | A tentative suggestion or model inference is stored as an approved decision. |
| F7 | Conflict loss | A new claim overwrites the old one and erases why the decision changed. |
| F8 | Integration gap | The agent does not invoke memory, or the invocation fails silently. |
| F9 | Scope/privacy leak | One repository, user, or task sees information belonging to another. |
| F10 | Operational failure | Concurrent writes, index corruption, or unavailable models lose or block memory access. |

### 2.1 Success criteria

The complete system should:

- preserve useful information across sessions and supported clients;
- attach checkable provenance and code evidence where applicable;
- distinguish verified, uncertain, conflicting, expired, and superseded knowledge;
- retrieve memories that answer the current question and abstain otherwise;
- make capture, validation, correction, deletion, and client use observable;
- improve or preserve coding outcomes at a measured and acceptable cost;
- work with deterministic local operation when optional model services are unavailable;
- give users control over storage scope, sensitive content, retention, export, and deletion.

These are product requirements. Specific performance targets will be selected before evaluation and should not be inferred from the current prototype results.

## 3. Scope and boundaries

### In scope

- Software-development workflows in local or explicitly configured repositories.
- Persistent knowledge across coding sessions and clients that use the 0xMemory interface.
- Code evidence and repository evolution, including branch and working-tree context.
- User-visible memory management and auditable lifecycle events.
- Local-first operation; optional model providers may assist capture or review.
- Evaluation on repository histories and multi-session coding tasks.

### Out of scope for the first complete research target

- Training or fine-tuning a model.
- Proving arbitrary natural-language claims true from code alone.
- Automatically treating every conversation turn or code edit as durable memory.
- Cross-organization hosted memory or multi-tenant cloud operation.
- Universal language parity before a language-specific evidence path is validated.
- Replacing Git, issue trackers, documentation, or source control as canonical records.

## 4. Memory taxonomy and lifecycle

The system should make memory kind and lifetime explicit. A single flat vector collection cannot represent these differences safely.

| Memory class | Examples | Typical lifetime | Main evidence |
|---|---|---|---|
| Project knowledge | Architecture decisions, conventions, subsystem facts | Until reviewed, superseded, or project ends | Code, tests, ADRs, configuration, explicit approval |
| Task state | Current objective, completed steps, blockers, relevant files | Task/session bounded; resolved at task completion | Tool activity, user request, current workspace |
| Episodic experience | A debugging path that worked, a prior migration pitfall | Reusable after applicability check; decay/review over time | Task outcome, tests, commits, user feedback |
| User preference | Preferred explanation style, workflow constraints | User-scoped, editable, explicitly removable | Direct user statement or confirmation |
| Environment/workflow | Test command, local setup constraints, deployment process | Until environment or process changes | Config files, successful execution, explicit owner |

Every memory has an immutable identifier and a sequence of lifecycle events. Updates create a new revision or a linked replacement; they do not erase the prior claim. Deletion is a user-controlled operation with a clear distinction between removing active content and retaining only the minimum audit record needed by the configured policy.

### 4.1 Required memory fields

At minimum, a memory record should represent:

- `id`, schema version, kind, claim, optional rationale, and answerable slots;
- scope: repository, branch, task, user, or explicitly global;
- provenance: source type, source reference, author/actor, timestamp, and capture method;
- trust basis: user-approved, directly observed, tool-verified, extracted candidate, or model-inferred;
- evidence references and the revision/branch/worktree against which they were checked;
- validity interval or expiry/review policy, importance, utility, and sensitivity labels;
- lifecycle state, conflict/supersession links, and an append-only event history;
- capture and review status, including the evidence and actor for a human decision.

Confidence and importance are separate. A frequently useful memory is not automatically more true. A model-generated confidence score is not a substitute for provenance or evidence.

## 5. System architecture

```text
User / coding agent
        │
        ├── MCP / CLI / editor integrations
        │       ├── recall (task + workspace context)
        │       ├── capture proposal / confirm / correct / forget
        │       └── inspect / review / export
        │
        ▼
Memory service
  ├── scope and policy checks
  ├── capture inbox and lifecycle ledger
  ├── repository context resolver
  ├── candidate generation and ranking
  ├── evidence validator and conflict detector
  ├── answerability / slot coverage / abstention
  └── audit events and usage feedback
        │
        ├── canonical local store (records + events)
        ├── rebuildable lexical / vector / code indexes
        └── optional LLM assistance for extraction or semantic review
```

The model must not be required on the retrieval hot path. Deterministic checks should handle scope, state filtering, evidence resolution, policy, and answerability features wherever possible. Optional LLM output is a proposal or advisory signal and must not silently override evidence or user decisions.

### 5.1 Canonical storage

The canonical record and lifecycle ledger must be durable and recoverable. Search indexes are derived data and must be rebuildable. Markdown remains valuable for inspection and portability; a transactional local database may be introduced if concurrent access, query cost, or atomic multi-record updates require it. The storage choice is an implementation decision to validate against workload requirements, not a goal by itself.

Required storage behavior:

- schema versioning and explicit migrations;
- atomic record and event updates;
- safe concurrent readers and writers or a documented single-writer coordinator;
- backup, restore, export, and index rebuild procedures;
- corruption detection and a recoverable read-only/degraded mode;
- no hidden loss of provenance during import or migration.

## 6. Capture and learning

### 6.1 Sources

Candidate memories may come from explicit user statements, accepted decisions, completed tasks, successful test/validation outcomes, approved documentation, and repository history. Source type must be retained. A commit message can suggest a decision; it does not prove that the decision remains valid.

### 6.2 Capture states

Use a two-stage flow for uncertain or extracted content:

1. Create a candidate with provenance, scope, evidence, sensitivity, and a concise claim.
2. Automatically accept only narrowly defined, policy-approved observations (for example, a directly observed tool result with a durable use case).
3. Keep inferred, ambiguous, sensitive, or decision-like claims in a reviewable inbox or request explicit confirmation.
4. On acceptance, attach evidence and validity policy; on rejection, record the rejection reason only if useful and permitted.

The system should avoid saving raw conversation transcripts by default. It should extract the smallest durable claim needed for future work and retain a source pointer rather than duplicating sensitive content.

### 6.3 Correction and forgetting

Users and agents need clear operations to revise a claim, mark it false, mark it no longer relevant, or forget it. Correction should create provenance and a lifecycle event. Forgetting must remove the active record and its derived index entries; the deletion policy must say whether minimal tombstone metadata remains and for how long. Export and deletion must include derived indexes and cached model artifacts where feasible.

## 7. Repository evidence and freshness

### 7.1 Evidence model

Evidence should be typed and resolvable: file, symbol, source span, test, configuration key, documentation section, commit, or an externally referenced artifact. Code anchors should record path, stable locator where possible, revision, content hash, and optional semantic hash. Evidence may be a set of supporting and contradicting references.

### 7.2 Validation context

Validation must identify the exact context: repository identity, branch, HEAD, merge base if relevant, and working-tree/index state. A memory valid on one branch may be false or unknown on another. Uncommitted changes must be considered when making a claim about the current working tree; if they cannot be examined, the result must say that validation is commit-only.

### 7.3 Tiered validation

Proposed validation order:

- **V0 — Resolve:** locate evidence across renames and confirm it belongs to the intended repository/revision.
- **V1 — Exact/semantic match:** compare hashes or a conservative syntax-aware representation. Normalization should avoid treating meaningful changes as cosmetic.
- **V2 — Deterministic probes:** run configured checks such as a symbol lookup, import/config query, or relevant test. Probes must be bounded and safe; execution is opt-in and sandboxed according to repository policy.
- **V3 — Advisory semantic review:** optionally ask a model to compare the claim with a bounded diff and evidence. Cache by claim and evidence revision, retain the rationale, and represent `unknown` explicitly.
- **Human review:** required for high-impact conflicts or ambiguous claims when policy says automated evidence is insufficient.

Validation results are `supported`, `contradicted`, or `unknown`, each with a reason and timestamp/revision. A changed anchor creates a review signal; it does not by itself prove the claim false. Automatic invalidation must be conservative, and false-verification and false-stale rates must both be measured.

### 7.4 Repository events

The service should support eager signals (Git hooks, editor events, or explicit observation) and just-in-time validation at recall. Hooks are optional accelerators, not the sole correctness mechanism. Missed hooks, branch changes, rebases, and unavailable clients must be covered by recall-time checks. Reverts may restore support, but should create a new event rather than erase the intervening state.

## 8. Retrieval, answerability, and use

### 8.1 Candidate generation

Combine lexical and semantic search with optional structural signals: active symbol proximity, import/call relationships, directory/subsystem, current task files, and recent task state. Use hard scope filters before ranking. Never allow a high semantic score to bypass repository, user, branch, privacy, or lifecycle boundaries.

### 8.2 Ranking

Ranking can combine query fit, task fit, evidence freshness, trust/provenance, scope match, utility from prior successful use, and time/importance policies. Decay should trigger review or lower priority, not silently rewrite truth. Ranking explanations should expose the dominant signals in developer tooling.

### 8.3 Answerability gate

Represent the requested information as answer slots (for example, current value, rationale, approver, date). A candidate may answer some slots and not others. Return only supported slots and make missing ones explicit. A semantic relatedness threshold alone is insufficient. If candidates fail answerability, conflict, or evidence checks, abstain with a concise reason and optionally point to a review-needed memory.

### 8.4 Context packing and response contract

Pack a bounded set of memories with claim, state, provenance/evidence pointers, relevant answer slots, and uncertainty. Respect actual model token limits when a tokenizer is available; otherwise label the budget as an approximation. The agent should distinguish recalled content from its own inference and avoid citing a memory as current if it is stale or unvalidated.

The system should record a structured retrieval receipt (query context, IDs considered/returned, validator outcomes, budget, and tool result) independently of whether the model chooses to render a user-facing receipt. Receipts must not include secret content by default.

## 9. Conflict, supersession, and lifecycle

Conflicts may be direct (claim A vs claim B), temporal (old vs new), contextual (branch or environment), or policy-based (approved exception vs general convention). Detect conflict candidates using claim slots, shared entities/anchors, and temporal/scope overlap. Model classification can propose a conflict but cannot resolve it alone.

Possible lifecycle states:

- `CANDIDATE` — awaiting capture review;
- `ACTIVE_VERIFIED` — supported in a stated context;
- `ACTIVE_UNVERIFIED` — usable with qualification under policy;
- `REVIEW_REQUIRED` — evidence changed or a conflict needs attention;
- `LIKELY_FALSE` — evidence or a probe contradicts the claim;
- `SUPERSEDED` — replaced by a reviewed successor;
- `ARCHIVED` — retained for history but not normal recall;
- `QUARANTINED` — unsafe, malformed, or suspicious content isolated;
- `DELETED` — removed according to retention policy.

Transitions require actor, timestamp, reason, and evidence. State exposure is a policy decision: low-risk unverified memories may appear with a warning; contradicted or quarantined memories should not be presented as current advice. Supersession is non-destructive and context-aware. A reverted code change does not automatically reinstate an old policy decision without checking its scope and approval.

## 10. Agent and user experience

### Agent interface

- `recall`: accepts task/question and available workspace context; returns bounded, qualified candidates and abstention reason.
- `propose_memory`: creates a candidate with source and evidence.
- `confirm_memory` / `review_memory`: accepts or rejects a candidate and records rationale.
- `correct_memory` / `supersede_memory`: records a reviewed change while preserving history.
- `forget_memory`: requests deletion according to policy.
- `inspect_memory` / `list_memories`: provides state, evidence, and provenance.
- `memory_status`: exposes storage, index, and integration health without returning private content.

Tool descriptions and client instructions can encourage correct use but do not enforce it. Integrations must be evaluated per client, and non-use or tool failure must be observable. Where supported, user-facing answers should identify memory-derived statements and distinguish them from fresh repository inspection.

### Human interface

Provide a way to inspect claims, evidence, scope, state, history, conflicts, and pending review; search and filter them; approve/correct/forget; and inspect capture/retrieval activity. Keep routine use unobtrusive. Require confirmation for destructive deletion only when necessary to prevent accidental loss, and make the effect clear.

## 11. Privacy, security, and trust

Memory is untrusted input and may contain stale, malicious, or instruction-like text. Retrieved memory must be treated as data, never as privileged system instructions. The design should include:

- explicit project/user/global scope separation and path canonicalization;
- secret detection and configurable exclusions for files and content classes;
- local-first defaults and clear controls before external model transmission;
- encryption-at-rest options appropriate to the deployment, with key ownership defined;
- retention, export, deletion, and backup policies;
- access controls for multi-user or shared-project deployments;
- safe rendering of memory text and bounded model prompts;
- audit events that avoid copying sensitive content unnecessarily;
- tests for prompt injection, cross-project retrieval, path traversal, poisoned memories, and deletion from indexes.

Repository files and commit messages can contain adversarial instructions. Extraction must preserve source trust and must not execute instructions found in retrieved content. Probes that run code or tests need explicit execution policy, timeouts, and resource limits.

## 12. Reliability, scale, and degraded behavior

The service should remain useful if an embedding model, LLM provider, parser, Git executable, or optional hook is unavailable. Lexical recall and direct inspection should remain available where safe. Failures must be visible in tool output and diagnostics; a failed validation must not be reported as verified.

Operational requirements include:

- atomic writes and concurrent session behavior;
- deterministic index rebuild and consistency checks;
- bounded retrieval latency and memory growth;
- schema migration/rollback strategy and compatibility with current Markdown data;
- crash recovery, backup/restore, and data integrity checks;
- instrumentation for capture, recall, validation, and failure rates;
- a documented single-project local baseline and explicit design for any later shared service.

## 13. Evaluation plan

Evaluation must separate memory quality from general model capability and report both component and end-to-end results.

### 13.1 Tracks

1. **Capture quality:** precision/recall of durable candidate memories, provenance completeness, unsupported-claim rate, review burden.
2. **Retrieval:** Recall@k, MRR/nDCG, answer-slot coverage, abstention precision/recall, hard-negative false positives.
3. **Freshness and conflict:** outdated-hit rate, false-stale rate, false-verification rate, conflict detection/resolution quality, time to detection, revert/branch correctness.
4. **Lifecycle and user control:** correction success, deletion completeness, history integrity, pending-review recall, user effort.
5. **Agent integration:** tool invocation and failure rates by client, context use, unsupported-memory reliance, receipt accuracy.
6. **Downstream coding:** task pass rate, regression tests, steps, tokens, latency, repeated errors, convention adherence, human edits.
7. **Privacy/security:** leakage and isolation tests, secret handling, adversarial memory behavior, deletion and export correctness.

### 13.2 Data and experimental controls

Use real repository histories and ordered multi-session coding tasks, plus clearly labeled synthetic fixtures for edge cases. Include refactors, semantic changes, uncommitted edits, branch divergence, reverts, renames, conflicting sources, missing attributes, no-answer queries, malicious content, and capture mistakes. Split by repository and freeze test sets before tuning.

Baselines should include no memory, full-history context where feasible, naive memory RAG, current 0xMemory, an evidence/JIT baseline, and the full proposed system. Use matched models, repository revisions, budgets, and task instructions. Report repeated runs, denominators, confidence intervals, failures, and component ablations. Compare total cost including extraction, validation, indexing, and retrieval.

No claim that memory improves coding performance should be made until downstream task results support it. Negative findings and client-specific integration limitations are part of the result.

## 14. Delivery plan and completion definition

The following is a dependency-oriented plan, not a commitment to implement all phases immediately.

| Phase | Deliverable | Completion evidence |
|---|---|---|
| P0 — Requirements and threat model | Approved taxonomy, policies, user stories, data boundaries, measurable targets | Reviewed requirements and unresolved-decision log |
| P1 — Durable ledger | Typed records, event history, migrations, export/restore, concurrency policy | Migration/recovery and data-integrity evaluation |
| P2 — Capture and control | Candidate inbox, provenance, confirmation, correction, deletion | Capture quality and deletion/control evaluation |
| P3 — Repository context | Branch/HEAD/worktree awareness, symbol/span anchors, conservative validator | Refactor/change/revert/branch evaluation |
| P4 — Retrieval and answerability | Task-aware candidate generation, evidence-qualified slot gate, abstention | Hard-negative and answerability evaluation |
| P5 — Conflict and maintenance | Conflict candidates, non-destructive supersession, dedupe/consolidation, expiry/review policies | Conflict quality, history integrity, review burden |
| P6 — Integration and UX | Auditable client adapters, management interface, health and failure reporting | Client-specific integration and usability evidence |
| P7 — Security and operations | Scope isolation, secret policy, safe probes, backup, degraded mode | Threat-model checks and operational recovery evidence |
| P8 — Research evaluation | Real-history and multi-session coding evaluation, baselines, ablations | Reproducible report with downstream outcomes and costs |

The system is complete for a declared deployment scope when every requirement in that scope has an implemented behavior, a failure mode, a user-control path, and evaluation evidence. A system may be complete for a local single-user Python workflow without claiming multi-user hosting or multi-language parity.

## 15. Open decisions for the next design review

1. Which memory classes are mandatory for the research contribution, and which are supporting product features?
2. Is the canonical format Markdown, SQLite, or a database-backed ledger with Markdown export? What concurrent workload must be supported?
3. Which capture categories may be accepted automatically, and which always require user confirmation?
4. What is the exact deletion and backup-retention policy, including audit tombstones and external model caches?
5. Which client integrations and languages define the evaluation target?
6. Which probes are allowed to execute, and what sandbox/consent model applies?
7. What branch policy governs memory validity across branches, forks, and worktrees?
8. Which answerability implementation is acceptable: slot rules, a learned/calibrated model, an LLM judge, or a measured combination?
9. What task benchmark and user-effort threshold will determine whether memory is beneficial?
10. Which capabilities are required for the first research release versus a later product-complete release?

## 16. Relationship to current prototype

The repository currently has a project-scoped Markdown source of truth, ChromaDB indexing, MCP/CLI/dashboard paths, explicit commit observation, file-level evidence links, manual verify/supersede operations, hybrid retrieval, and an opt-in relevance gate. Its documentation reports limitations including no automatic working-tree observation, no code-structure indexing, one-writer assumptions, exact-duplicate-only suppression, approximate token budgeting, and evaluation that does not establish downstream coding-task gains.

The supplied v2 design adds a concrete direction for symbol-level anchors, tiered/JIT validation, graded exposure, answer slots, a lifecycle ledger, maintenance, and real-history evaluation. This document retains those ideas and broadens the requirements to cover capture governance, task-state and preference memory, user correction/deletion, branch/worktree context, privacy/security, multi-session reliability, observability, and complete-loop evaluation.

All capabilities described in Sections 4–14 are design proposals unless explicitly identified above as current prototype behavior. No v2 or complete-system performance result is claimed here.
