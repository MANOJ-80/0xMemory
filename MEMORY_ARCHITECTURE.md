# 0xMemory Architecture: Evidence-Grounded Memory for Coding Agents

This document explains the architecture implemented on
`architecture/evidence-grounded-memory`. It describes the current prototype,
not every capability in the broader design proposal. The install and run guide
is in [README.md](README.md); the full requirements are in
[DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md).

## The core mental model

**A memory is a scoped claim with a history and, when it describes code, anchors
to the repository evidence that was reviewed.** It is not simply a text chunk
that happens to have a high vector similarity.

Each memory answers four questions:

1. **What is being claimed?** The text, type, and any structured answer slots.
2. **Where and when does it apply?** Project, branch, task, or user scope; plus
   optional expiry and review dates.
3. **Why should an agent trust or qualify it?** Source provenance, trust basis,
   lifecycle state, and sensitivity.
4. **What evidence supports it?** Git commit, repository-relative file paths,
   and optional Python symbol anchors with content and syntax-aware hashes.

The governing rule is: **a code change raises a review signal; it does not,
by itself, prove a natural-language claim false.** At recall time, 0xMemory
checks the claim's recorded context against the current repository and either
returns supporting status, an explicit unknown/review warning, or suppresses
evidence that is contradicted by its available symbol checks. A human or agent
then verifies the claim or writes a reviewed successor while preserving the old
revision.

```text
Capture claim → attach provenance and scope → add code anchors when reviewed
       ↓
Candidate review (for inferred/uncertain capture)
       ↓
Hard policy filters → hybrid ranking → evidence check → answerability gate
       ↓
Bounded, qualified context OR an explicit abstention
       ↓
Observe change → review → verify, supersede, archive, or forget
```

## What is stored

The canonical records are human-readable Markdown files under
`.0xmemory/memory/`. A rebuildable ChromaDB index supports semantic search when
available. A separate `events.jsonl` records lifecycle and recall metadata in a
SHA-256 hash chain; recall events store a query hash and returned IDs, not the
raw query text.

| Memory kind | Typical use | Scope/lifetime behavior |
| --- | --- | --- |
| Fact | Current code or project fact | Project or branch; link code evidence when useful |
| Decision | Chosen design and rationale | Preserve prior versions when superseded |
| Learning | Reusable gotcha or debugging result | Candidate review is available for uncertain extraction |
| Preference | Developer workflow preference | May be scoped to a user ID, but storage remains project-local today |
| Task state | Resumable progress, blocker, next step | Requires a task ID; expires after seven days by default |
| Environment | Toolchain, test command, setup workflow | Should be reviewed when environment evidence changes |

Records carry provenance, trust basis, evidence references, answer slots,
sensitivity, expiry/review metadata, utility feedback, and revisions. Captured
or extracted candidates are not ordinary recall results until accepted. An
accepted candidate is `active_unverified`; rejection quarantines it.

## How code evidence and evolution work

When a memory is linked to a Git commit and file, 0xMemory records the commit's
blob identity. When a Python symbol is supplied, it also records the symbol's
source hash and an AST-based semantic hash. That semantic hash ignores line
numbers and leading docstrings, so formatting or documentation-only edits need
not make a symbol appear different. It is a structural comparison, not proof
that the prose claim follows from the code.

Evidence is assessed against repository identity, current branch and HEAD,
commit ancestry, changed paths, staged/unstaged/untracked paths, renames, and
available symbol anchors. A symbol whose syntax changed is marked unknown for
review; the system does not ask a model to decide whether arbitrary prose is
true. Python is the only language with syntax-aware anchors in this prototype.

`observe_commit` is explicit and idempotent for the same observed commit. There
is no background watcher or Git hook. A changed linked file moves an active
record to `review_required` and records the observation. Review-required records
can still be returned with an evidence warning; contradicted symbol checks are
not presented as current advice. Explicit `verify` changes the state to
`active_verified`. `supersede` adds a linked successor and keeps the old record
as history. Editing claim wording also sends it back to review.

## How retrieval works

Recall follows these stages:

1. **Eligibility filter.** Exclude out-of-scope branch/task/user records,
   expired records, candidates, quarantined or superseded records, secrets,
   and sensitive records unless explicitly included. These filters happen
   before ranking, so a semantic match cannot cross a scope or privacy boundary.
2. **Candidate ranking.** Combine lexical and optional vector ranking with
   file/symbol matches and task context. Reciprocal-rank fusion contributes
   `weight / (60 + rank)` per source. A linked file or symbol is given an
   additional ranking contribution. Past helpful/not-helpful feedback adjusts
   utility slightly; utility does not change trust or evidence state.
3. **Evidence qualification.** Check the repository anchors. Contradicted
   evidence is removed; unknown evidence remains qualified with a warning.
4. **Answerability gate.** Detect a small set of requested slots from question
   wording (currently rationale, approver, date, and location). A record must
   contain each requested slot and have lexical support in its claim or slot
   values. If no record passes, return an abstention instead of dressing up a
   merely related memory as an answer.
5. **Context packing.** Pack claims, provenance, evidence status, retrieval
   reasons, and only the relevant requested answer slots within a bounded
   budget. The current budget is measured in UTF-8 bytes as a conservative
   approximation, not model-token counts. Retrieved memory is labeled as
   untrusted data.

The relevance gate based on a minimum semantic similarity remains opt-in and is
disabled by default; the repository's reserved evaluation did not show it
solving no-answer retrieval.

## Conflict, privacy, and maintenance

Conflict discovery is a **candidate generator**. It compares memories sharing
files, symbols, or tags, then uses Jaccard overlap of normalized content tokens
to report possible duplicates or conflicts. It never decides which claim is
true, merges records, or silently deletes history.

Credential checks are deterministic pattern checks for common obvious formats,
not a general secret scanner. Secret-labeled records are refused. Sensitive
records are excluded from routine recall, listing, export, and the review queue
unless enabled by the caller. These labels and regular expressions cannot
guarantee that every private value is detected.

The review queue collects capture candidates, changed claims, expired records,
and overdue review dates. Task completion archives task-scoped records. Delete
removes a record from Markdown and the derived vector index; the compact event
ledger can still contain an event identifier and action. Users can export and
re-import JSON records without overwriting colliding IDs.

## What makes this approach different

Many memory tools address one or more of: storing long histories, extracting
compact facts, connecting entities in a graph, or managing what stays in an
agent's active context. 0xMemory's distinguishing design choice is to center
**repository evolution and evidence state**: a code-related memory says which
branch/commit/files/symbols it was checked against, how current changes affect
that evidence, and whether an agent should qualify the claim.

This is a difference in emphasis and data model, not a claim that other systems
cannot store metadata or that 0xMemory is better for every workload.

| Approach/system | Primary memory model | 0xMemory's relationship and trade-off |
| --- | --- | --- |
| Basic vector RAG | Embed text chunks, retrieve by semantic similarity, and place matches in context | 0xMemory also uses semantic retrieval, but adds typed lifecycle states, hard scope/sensitivity filters, Git evidence checks, answer slots, and abstention. Its extra checks add complexity and do not prove arbitrary prose true. |
| [Mem0](https://docs.mem0.ai/open-source/overview) | A memory engine exposed as a library or self-hosted server, with configurable LLM, embedder, vector store, and reranker; its platform documentation describes entity-graph links that boost hybrid retrieval | Both extract/store/retrieve durable memories. Mem0 emphasizes flexible user/app memory and entity connections; 0xMemory emphasizes local project records and code evidence across Git changes. 0xMemory currently lacks Mem0's entity graph and managed/self-hosted product surface. |
| [Zep / Graphiti](https://help.getzep.com/v4/graphiti/getting-started/overview) | Temporal knowledge graphs with entities, relationships, episodes, historical validity, and hybrid time/full-text/semantic/graph retrieval | Both model evolving facts and trace source context. Zep/Graphiti focuses on graph relationships and multi-source subject context; 0xMemory uses explicit code anchors and a review lifecycle for repository claims. 0xMemory has no temporal graph, graph traversal, or managed governance plane. |
| [Cursor Memories](https://docs.cursor.com/en/context/memories) and [Rules](https://docs.cursor.com/context/rules-for-ai) | Conversation-derived project memories and reusable rules, with background extraction and user approval for generated memories | Both carry project knowledge across sessions. Cursor emphasizes injecting memories/rules into its own agent context; 0xMemory emphasizes portable records, evidence qualification against Git changes, and retrieval through MCP/CLI. Cursor's automatic capture is more passive; 0xMemory's capture and commit observation are explicit in this prototype. |
| [Letta Code memory](https://docs.letta.com/configuration/memory) | Agent-managed, Git-backed memory files and background memory maintenance | Both support durable, inspectable memory. Letta focuses on the stateful agent and how it manages its context and memory files; 0xMemory is a project-local memory service that can be called by separate MCP clients. 0xMemory does not manage the model's active context window or run background “dreaming.” |
| [MemGPT paper](https://arxiv.org/abs/2310.08560) | Research model for agent-controlled movement between context and external memory as virtual context management | MemGPT is a related antecedent in virtual context management, not the same product or architecture as current Letta Code. 0xMemory does not page information into and out of the model's active context window. |

These systems solve adjacent problems, and the comparison is not a benchmark.
The links above describe their current documented approaches as checked on
2026-10-28; product capabilities can change. A fair empirical comparison would
use the same repositories, tasks, models, context budget, and evaluation set.

## Current boundaries and next steps

This is a local, project-scoped prototype with a single-writer assumption. It
does not yet provide cross-project user memory, transactional multi-writer
storage, continuous Git/editor observation, broad language-specific anchors,
automated semantic conflict resolution, or a tested migration/recovery system
for every failure mode. User-scope IDs currently filter memories inside the
project's store; they do not create a shared user store across repositories.

The implementation's core flows have deterministic smoke coverage, but this
prototype has not established end-to-end coding-performance gains through a
multi-repository study. See [the evaluation notes](evaluation/README.md) for
existing synthetic pipeline measurements and their limitations.
