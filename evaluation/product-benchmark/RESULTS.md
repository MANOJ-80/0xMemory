# GEDAM vs no persistent memory: benchmark results

**Run date:** 2026-10-30 (Asia/Kolkata)  
**Status:** Exploratory paired pilot completed.  
**Full protocol:** [README.md](README.md)  
**Reproduce:** [run_pilot.py](run_pilot.py), [run_retrieval_pilot.py](run_retrieval_pilot.py), [codex_usage_adapter.py](codex_usage_adapter.py)  
**Raw run records:** [coding pilot JSON](pilot/raw-results.json), [retrieval diagnostic JSON](pilot/retrieval-results.json)

## Summary

On this small, deliberately memory-dependent synthetic coding pilot, GEDAM passed the hidden checks in **6/6 runs**; the no-memory condition passed **0/6**. These are two repetitions of each of only three task families, so the six runs per arm are not six independent tasks. This is evidence that the supplied prior-session facts were retrieved and useful on these fixtures; it does not establish a general production success-rate advantage.

GEDAM retrieved all three current, relevant records in the separate retrieval diagnostic and correctly withheld stale, candidate, unresolved-conflict, and irrelevant records in the tested cases. The Codex CLI reported fewer aggregate input tokens in the GEDAM coding runs, but those turn totals include harness/runtime context and varied substantially between runs. Treat the token difference as descriptive only; the experiment does not establish token savings or cost reduction.

## Paired coding-agent pilot

Three tiny repository tasks require a decision present in a synthetic prior-session memory: TOML plus `SERVICE_PORT` override, an event pagination contract, and a 64-entry LRU cache. Each task ran twice per condition, in randomized condition order. The coding agents received the same objective and repository skeleton; the GEDAM condition also received the retrieved memory context. Tests were run after the agent stopped.

| Task family | GEDAM | No memory |
| --- | ---: | ---: |
| TOML config and environment override | 2/2 | 0/2 |
| Event pagination contract | 2/2 | 0/2 |
| Worker result cache policy | 2/2 | 0/2 |
| **Overall runs** | **6/6 (100%)** | **0/6 (0%)** |

The raw point difference is +100 percentage points (6/6 vs 0/6). With only three independent task families, a population confidence interval or significance claim would be misleading, so none is reported. The task suite is intentionally designed to require cross-session facts; this favors a memory-enabled system by construction and is a feasibility pilot, not a balanced estimate of ordinary coding-task performance.

### Task-level outcomes

| Outcome | GEDAM | No memory |
| --- | ---: | ---: |
| Hidden deterministic check passed | 6/6 | 0/6 |
| Agent process completed successfully | 6/6 | 6/6 |
| Usage event captured | 6/6 | 6/6 |
| Usage coverage | 100% (6/6) | 100% (6/6) |
| Mean agent runtime per run | 25.9 s | 27.1 s |
| Mean retrieved-memory context estimate | 323 tokens | 0 tokens |
| Mean retrieved-memory bytes | 968 bytes | 0 bytes |

All agent process return codes were successful; task success is scored only from the post-run deterministic assertions. GEDAM context estimates use the product's UTF-8 byte-count-divided-by-three heuristic, not a model tokenizer. The context estimate covers packed retrieved context only, not the full agent prompt.

## Token and context usage

Codex CLI was pinned to `gpt-6-luna` with `codex-cli 0.163.0-alpha.11.1`. Values below are sums and means of the six completed `turn.completed.usage` events per condition. They are Codex-reported **agent-turn counters**, not per-request billing records. No monetary cost was exposed or inferred.

| Counter | GEDAM: total (mean/run) | No memory: total (mean/run) | Descriptive difference in mean |
| --- | ---: | ---: | ---: |
| Input tokens | 478,673 (79,779) | 515,706 (85,951) | −7.2% |
| Cached input tokens | 440,960 (73,493) | 436,352 (72,725) | +1.1% |
| Cache-write input tokens | 0 (0) | 0 (0) | 0% |
| Output tokens | 5,433 (906) | 5,583 (931) | −2.7% |
| Reasoning output tokens | 1,361 (227) | 2,087 (348) | −34.8% |

Input counters include agent/runtime overhead and varied widely across these six runs; the paired run-level values are preserved in the raw JSON. Cached input is shown as its own reported counter and is not subtracted from input. These aggregate differences should not be interpreted as a causal token reduction, cost saving, or reliable efficiency win. The measured GEDAM memory context itself added an estimated mean of 323 tokens per follow-up run; setup-session extraction/write usage was not measured because records were seeded manually.

Model context-window utilization, per-HTTP-request tokens, provider invoice cost, cost per successful task, memory extraction tokens, and all-in setup-plus-follow-up tokens are **not measured**. No value was substituted for missing cost information.

## Retrieval, validity, suppression, and abstention

A separate seven-case diagnostic exercised the production GEDAM `recall_context` path with keyword retrieval (embeddings disabled). The cases and expected IDs/states are recorded in [retrieval-results.json](pilot/retrieval-results.json). The gold labels were written into these synthetic fixtures; they were not independently annotated.

| Metric | GEDAM result | Denominator |
| --- | ---: | ---: |
| Recall@5 | 3/3 (100%) | Three answerable current-memory queries |
| MRR | 1.00 | Same three queries; each relevant record ranked first |
| Precision@5 | 3/3 (100%) | Three returned records across those queries |
| Valid-memory suppression | 0/3 (0%) | Three current valid relevant records available |
| Stale-hit rate | 0/1 (0%) | One query with a stale record available |
| Stale-record suppression | 1/1 (100%) | One stale record tested |
| Candidate suppression | 1/1 (100%) | One unapproved candidate tested |
| No-answer false-positive rate | 0/1 (0%) | One query with no relevant answer available |
| Correct no-answer abstention | 1/1 (100%) | Same no-answer query |
| Conflict handling | 1/1 correctly abstained | One unresolved conflicting-claim query |
| Context-budget compliance | 7/7 (100%) | Seven diagnostic queries; 800 estimated-token limit |
| Mean context for positive queries | 161 estimated tokens | Three relevant-memory queries |
| Useful context density | 6.21 relevant facts / 1,000 estimated tokens | Three packed contexts |

The no-memory arm has no persistent records by definition. On the three answerable queries, it therefore exposes 0/3 relevant facts and omits 3/3 facts; report that as the treatment's absence of memory, not as a failure of a retrieval algorithm. For no-answer tasks, an empty context abstains by construction. The conflict diagnostic assesses retrieval-time abstention only, not whether a language model would answer safely.

## Interpretation and limits

The pilot demonstrates a clear result on the constructed tasks: GEDAM surfaced the seeded prior-session decisions, and the coding agent used them to satisfy the hidden checks. It also shows clean diagnostic outcomes on a handful of stale, candidate, conflict, and no-answer fixtures. This supports continuing to a larger evaluation; it does not show that GEDAM is universally better or ready for a paper-level efficacy claim.

Key limits:

- Only three synthetic task families and two repetitions per condition; task families, not repeated runs, are the independent units.
- The task prompts deliberately ask for decisions that only the GEDAM memory arm receives, so baseline task failure is expected by design.
- Memory records were manually seeded. Capture, extraction, deduplication, lifecycle updates, and memory-write quality were not tested.
- Retrieval labels were fixture-authored, with one example each for stale, candidate, no-answer, and conflict behavior; the diagnostic percentages are not robust estimates.
- Only one model/harness and one local environment were used. The agent-turn token counters include Codex overhead and do not expose billed cost.
- No blinded human patch rubric, regression suite, broader repository sample, context-pressure sweep, or independent adjudication was run.

For a defensible general claim, run the preregistered protocol in [README.md](README.md) on a larger frozen suite spanning multiple repository families, include distractor/no-answer/control tasks, independently review the labels, and account for setup plus follow-up token usage. Do not generalize the 6/6 pilot outcome beyond these fixtures.
