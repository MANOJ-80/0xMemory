# GEDAM Full Benchmark Results

## Paper-ready primary metrics

Use this section as the concise results summary. The underlying experiments are distinct and should not be pooled: the lifecycle suite evaluates synthetic memory validity scenarios, LoCoMo evaluates evidence retrieval, the 26-case suite evaluates abstention/conflicts, and the agent pilot records actual Codex usage counters.

### Memory validity and lifecycle (32 held-out checkpoints)

| Method | Recall@k (answerable, n=20) | Outdated hit (n=12) | Valid-memory suppression (n=20) | No-answer false positives (n=12) | Correct update (n=5) |
|---|---:|---:|---:|---:|---:|
| No memory | 0/20 (0%) | 0/12 (0%) | 20/20 (100%) | 0/12 (0%) | 0/5 (0%) |
| Basic retrieval | 19/20 (95%) | 12/12 (100%) | 1/20 (5%) | 9/12 (75%) | 0/5 (0%) |
| Lifecycle baseline | 19/20 (95%) | 7/12 (58.3%) | 1/20 (5%) | 9/12 (75%) | 5/5 (100%) |
| **GEDAM v3** | **13/20 (65%)** | **2/12 (16.7%)** | **7/20 (35%)** | **4/12 (33.3%)** | **5/5 (100%)** |

GEDAM cuts outdated hits by 41.6 percentage points versus the lifecycle baseline and no-answer false positives by 41.7 points. The trade-off is a 30-point decrease in answerable recall versus the lifecycle baseline and 30 points more valid-memory suppression. This is the key lifecycle result and limitation.

### Context and token usage

| Measurement | GEDAM | Comparator | Difference |
|---|---:|---:|---:|
| LoCoMo mean rendered context | 442.8 exact tokens | Basic: 501.0 exact tokens | −11.6% |
| LoCoMo mean rendered context | 442.8 exact tokens | Similarity: 126.5 exact tokens | +250.2% |
| LoCoMo mean rendered context | 442.8 exact tokens | Full history: 21,221.6 exact tokens | −97.9% |
| Agent pilot mean input usage | 79,779 provider-reported tokens/run | No memory: 85,951/run | −7.2% descriptive |
| Agent pilot mean output usage | 906 provider-reported tokens/run | No memory: 931/run | −2.7% descriptive |
| Agent pilot mean reasoning usage | 227 provider-reported tokens/run | No memory: 348/run | −34.8% descriptive |
| Agent pilot retrieved memory context | 323 estimated tokens/run | No memory: 0 | +323 tokens |

LoCoMo counts are exact `cl100k_base` tokens for the rendered memory/context payload. Agent pilot figures are Codex-reported turn usage, include harness/runtime overhead, and come from six runs per arm on three synthetic task families. They are exploratory and do not establish a causal cost saving. Provider invoice cost, memory-write/extraction tokens, and full model context-window utilization were not measured.

### LoCoMo evidence retrieval (10 conversations, 1,986 questions)

| Method | Recall@5 | MRR | Precision@5 | Irrelevant rate | Mean context tokens |
|---|---:|---:|---:|---:|---:|
| No memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 |
| Similarity | **0.499** | **0.432** | 0.115 | 0.885 | 126.5 |
| Basic memory | 0.437 | 0.377 | 0.101 | 0.899 | 501.0 |
| **GEDAM v3** | 0.410 | 0.262 | **0.106** | **0.817** | 442.8 |
| Full history | 0.804 | 0.031 | 0.004 | 0.996 | 21,221.6 |

On LoCoMo, GEDAM has the lowest irrelevant rate among the memory retrieval methods and slightly higher precision than basic memory, while lexical similarity has stronger recall and MRR. Do not claim GEDAM leads on all retrieval metrics.

### Labeled abstention and conflict cases (26 cases)

| Method | Answer recall | False abstention | No-answer FP rate | Correct abstention | Conflict detection recall |
|---|---:|---:|---:|---:|---:|
| No memory | 0.000 | 1.000 | 0.000 | 1.000 | 0/1 |
| Basic memory | 0.769 | 0.154 | 0.846 | 0.154 | 0/1 |
| Similarity | 0.769 | 0.154 | 0.846 | 0.154 | 0/1 |
| **GEDAM v3** | **0.615** | **0.308** | **0.692** | **0.308** | **1/1** |

Conflict estimate is one labeled conflict case and is therefore a case result, not a stable rate. All labeled fixtures are synthetic and authored for the benchmark.

## 1. Executive summary

GEDAM v3 was evaluated against no memory, basic memory, and lexical similarity retrieval. The main benchmark uses all 10 LoCoMo conversations and 1,986 QA items. A separate 26-case labeled safety suite measures abstention, no-answer behavior, and conflict detection.

GEDAM improved its LoCoMo recall from the previous 0.205 to **0.410** after fixing answer-slot gating and increasing direct lexical relevance weighting. It reduces irrelevant retrieval compared with the basic memory and similarity arms, uses fewer context tokens than basic memory, and detects all labeled conflicts. Similarity retrieval still has the highest raw positive recall; GEDAM should therefore be presented as a validity, suppression, conflict, and context-control architecture rather than as the highest-recall retriever.

## 2. LoCoMo benchmark protocol

- Dataset: LoCoMo 10, official release: <https://github.com/snap-research/LoCoMo>
- Dataset paper: <https://aclanthology.org/2024.acl-long.747/>
- Conversations: 10
- QA items: 1,986
- Retrieval cutoff: top-k=5
- Tokenizer: `cl100k_base`
- Dataset SHA-256: `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`
- Evaluation unit for confidence intervals: conversation-level clustered bootstrap
- Bootstrap draws: 4,000; seed `20261030`

Arms:

1. `no_memory`: empty context control.
2. `similarity`: deterministic lexical TF-IDF-like observation retriever.
3. `basic`: existing 0xMemory baseline ranker.
4. `gedam`: GEDAM ranker with relevance gating, lifecycle scoring, conflict handling, and adaptive context packing.

## 3. Main retrieval and context results

| Method | Recall@5 | MRR | Precision@5 | Evidence recall-any | Irrelevant rate | Answer-evidence F1 | Mean context tokens | Compression vs full history |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| No memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 100.0% |
| Similarity | 0.499 | 0.432 | 0.115 | 0.549 | 0.885 | 0.028 | 126.5 | 99.4% |
| Basic memory | 0.437 | 0.377 | 0.101 | 0.484 | 0.899 | 0.007 | 501.0 | 97.6% |
| **GEDAM v3** | **0.410** | **0.262** | **0.106** | **0.455** | **0.817** | **0.007** | **442.8** | **97.8%** |
| Full history reference | 0.804 | 0.031 | 0.004 | 0.840 | 0.996 | 0.000 | 21,221.6 | 0.0% |

### Absolute comparisons

- GEDAM recall improved by **0.205** over the previous implementation.
- GEDAM reduces irrelevant retrieval by **8.1 percentage points** versus basic memory.
- GEDAM reduces irrelevant retrieval by **6.7 percentage points** versus similarity.
- GEDAM uses **58.2 fewer tokens per query** than basic memory, a **11.6% reduction**.
- GEDAM compresses the full dialogue by **97.8%** on average.
- Full history has high evidence coverage but carries approximately **21.2k tokens per query** and a very high irrelevant rate.

## 4. Clustered bootstrap differences

Values are `GEDAM − comparison arm`; intervals are 95% conversation-cluster bootstrap confidence intervals.

| Metric | GEDAM − Similarity | GEDAM − Basic | GEDAM − Full history |
|---|---:|---:|---:|
| Recall@5 | −0.089 [−0.111, −0.069] | −0.026 [−0.039, −0.015] | −0.394 [−0.432, −0.358] |
| MRR | −0.170 [−0.194, −0.146] | −0.116 [−0.133, −0.099] | +0.229 [+0.212, +0.248] |
| Precision@5 | −0.010 [−0.019, −0.001] | +0.005 [−0.000, +0.011] | +0.101 [+0.093, +0.108] |
| Evidence recall-any | −0.096 [−0.122, −0.073] | −0.028 [−0.041, −0.016] | −0.385 [−0.423, −0.350] |
| Irrelevant rate | −0.066 [−0.080, −0.053] | −0.081 [−0.092, −0.070] | −0.176 [−0.189, −0.163] |
| Context tokens | +317.7 [+310.3, +325.5] | −57.0 [−63.7, −49.6] | −20,383.1 [−22,461.8, −18,004.7] |

## 5. Labeled validity and safety benchmark

This separate suite contains 26 labeled cases covering answerable queries, no-answer queries, paraphrases, temporal claims, and contradictory claims.

| Method | Answer recall | False abstention | No-answer false-positive rate | Correct abstention | Conflict detection recall |
|---|---:|---:|---:|---:|---:|
| No memory | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| Basic memory | 0.769 | 0.154 | 0.846 | 0.154 | 0.000 |
| Similarity | 0.769 | 0.154 | 0.846 | 0.154 | 0.000 |
| **GEDAM v3** | **0.615** | **0.308** | **0.692** | **0.308** | **1.000** |

GEDAM detects every labeled conflict and lowers no-answer false positives relative to basic and similarity retrieval. It still has lower answer recall on this small safety suite, showing that further semantic candidate expansion is a useful next optimization.

## 6. Memory validity metrics

| Metric | LoCoMo | Labeled safety suite | Interpretation |
|---|---|---|---|
| Stale-hit rate | N/A | Not included | Requires explicit expired/deleted memory labels. |
| Valid-memory suppression | N/A | Not included | Requires labeled valid memories that must remain retrievable. |
| No-answer false-positive rate | N/A | Measured | LoCoMo questions are answer-bearing; safety suite provides negative queries. |
| Correct abstention | N/A | Measured | Requires a no-answer label. |
| Conflict resolution accuracy | N/A | Conflict detection recall 1.000 for GEDAM | Requires contradictory claim pairs. |
| Evidence recall and precision | Measured | Measured | LoCoMo evidence IDs provide positive retrieval labels. |

## 7. Token and context accounting

All LoCoMo context counts are exact rendered-payload counts using `cl100k_base`.

| Method | Mean context tokens | Mean source tokens | Compression |
|---|---:|---:|---:|
| No memory | 0.0 | 21,221.6 | 100.0% |
| Similarity | 126.5 | 21,221.6 | 99.4% |
| Basic memory | 501.0 | 21,221.6 | 97.6% |
| GEDAM v3 | 442.8 | 21,221.6 | 97.8% |
| Full history | 21,221.6 | 21,221.6 | 0.0% |

These are context-token measurements. Provider billing tokens, generated answer tokens, and monetary cost require a separate pinned-model generation run with provider usage counters; they are not inferred from context length.

## 8. Architecture changes made

1. **Answer-slot gating fix:** unstructured memories are no longer rejected merely because they lack normalized fields such as `date` or `location`.
2. **Adaptive lexical relevance:** GEDAM now retains a direct query-memory overlap signal instead of relying mainly on compressed reciprocal-rank values.
3. **Paraphrase tolerance:** the relevance gate now requires fewer shared informative terms for longer natural-language questions.
4. **Lower EDAM floor:** the default minimum EDAM score was reduced from `0.22` to `0.12` so low-salience but relevant facts are not discarded before ranking.
5. **Rebalanced ranking:** relevance receives more weight, while scope and utility receive less, improving question-specific retrieval.

## 9. Reproducibility artifacts

- Full raw LoCoMo results: `run-v3/results.json`
- LoCoMo aggregate CSV: `run-v3/summary.csv`
- LoCoMo report: `RESEARCH_REPORT_V3.md`
- Validity raw results: `validity-run-v4/results.json`
- Validity report: `validity-run-v4/REPORT.md`
- Benchmark runner: `locomo_benchmark.py`
- Validity runner: `validity_benchmark.py`
- Bootstrap report generator: `paper_report.py`

## 10. Research interpretation

The results support a specific claim: GEDAM provides stronger memory control than basic retrieval by reducing irrelevant memories, reducing context relative to basic memory, and detecting contradictory claims. The results do not support claiming that GEDAM has the highest raw recall on LoCoMo. Similarity retrieval remains the recall leader, while GEDAM provides a more selective and validity-aware retrieval policy.

## 11. Lifecycle memory benchmark

This is the memory-specific synthetic commit-aware benchmark that directly measures stale-memory handling, valid-memory suppression, no-answer behavior, update correctness, evidence state, and budgeted recall. It uses 32 held-out checkpoints with the same corpus, query, file hints, and task for every condition.

| Condition | Checkpoints | Recall@k | Budgeted recall | MRR | Outdated hit | Outdated rate | Valid suppression | No-answer FP | Update correct |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| No memory | 32 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| Basic retrieval | 32 | 0.950 | 0.950 | 0.950 | 1.000 | 1.000 | 0.050 | 0.750 | 0.000 |
| Lifecycle baseline | 32 | 0.950 | 0.950 | 0.950 | 0.583 | 0.583 | 0.050 | 0.750 | 1.000 |
| **GEDAM / EDAM** | **32** | **0.650** | **0.650** | **0.650** | **0.167** | **0.167** | **0.350** | **0.333** | **1.000** |

Interpretation: GEDAM suppresses outdated memories much more effectively than basic and lifecycle-only baselines, and it improves no-answer false positives from 0.750 to 0.333. The trade-off is lower recall and higher valid-memory suppression on this small keyword/file-proxy suite. The held-out suite is fixture-authored and should be described as an exploratory lifecycle evaluation, not a population estimate.

## 12. Direct GEDAM retrieval diagnostic

The paired retrieval diagnostic contains seven targeted cases.

| Metric | GEDAM | Denominator |
|---|---:|---:|
| Recall@5 | 3/3 (100%) | Three answerable current-memory queries |
| MRR | 1.00 | Same three queries |
| Precision@5 | 3/3 (100%) | Returned records on answerable queries |
| Valid-memory suppression | 0/3 (0%) | Three valid relevant memories |
| Stale-hit rate | 0/1 (0%) | One stale-memory query |
| Stale-record suppression | 1/1 (100%) | One stale record |
| Candidate suppression | 1/1 (100%) | One unapproved candidate |
| No-answer false-positive rate | 0/1 (0%) | One no-answer query |
| Correct no-answer abstention | 1/1 (100%) | Same query |
| Conflict handling | 1/1 correctly abstained | One unresolved conflict |
| Context-budget compliance | 7/7 (100%) | 800 estimated-token limit |
| Mean positive-query context | 161 estimated tokens | Three positive queries |
| Useful context density | 6.21 facts / 1,000 tokens | Three positive queries |

## 13. Agent token and context pilot

The paired coding-agent pilot ran three synthetic memory-dependent task families twice per condition. These are provider-reported Codex agent-turn counters, not inferred estimates.

| Counter | GEDAM total (mean/run) | No memory total (mean/run) | Mean difference |
|---|---:|---:|---:|
| Input tokens | 478,673 (79,779) | 515,706 (85,951) | −7.2% |
| Cached input tokens | 440,960 (73,493) | 436,352 (72,725) | +1.1% |
| Output tokens | 5,433 (906) | 5,583 (931) | −2.7% |
| Reasoning output tokens | 1,361 (227) | 2,087 (348) | −34.8% |
| Mean retrieved-memory context | 323 estimated tokens | 0 | +323 tokens |
| Mean runtime | 25.9 s | 27.1 s | −1.2 s |
| Hidden checks passed | 6/6 | 0/6 | +6 runs |

The pilot is intentionally small and memory-dependent. Agent-turn counters include harness/runtime overhead; they are descriptive and do not establish provider cost savings. Setup-session extraction/write usage and invoice cost were not measured.

## 14. Source reports for memory metrics

- Lifecycle benchmark: `evaluation/research-benchmark/held-out-keyword/REPORT.md`
- Lifecycle raw results: `evaluation/research-benchmark/held-out-keyword/results.json`
- Agent token pilot: `evaluation/product-benchmark/RESULTS.md`
- Agent pilot raw usage: `evaluation/product-benchmark/pilot/raw-results.json`
- Retrieval diagnostic: `evaluation/product-benchmark/pilot/retrieval-results.json`
