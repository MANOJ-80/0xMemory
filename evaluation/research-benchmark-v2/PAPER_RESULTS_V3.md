# Paper-ready end-to-end results (GEDAM v3)

We reran the benchmark after correcting two GEDAM failure modes: overly strict answer-slot gating for unstructured memories and weak lexical relevance weighting. The LoCoMo run covers all 10 conversations and 1,986 QA items with top-k=5 and exact `cl100k_base` token counts.

| Method | Recall@5 | MRR | Precision@5 | Irrelevant rate | Context tokens | Compression |
|---|---:|---:|---:|---:|---:|---:|
| No memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 100.0% |
| Similarity | 0.499 | 0.432 | 0.115 | 0.885 | 126.5 | 99.4% |
| Basic memory | 0.437 | 0.377 | 0.101 | 0.899 | 501.0 | 97.6% |
| **GEDAM v3** | **0.410** | **0.262** | **0.106** | **0.817** | **442.8** | **97.8%** |

GEDAM reduces irrelevant retrieval by 8.1 percentage points relative to basic memory and 6.7 points relative to similarity. It uses 11.6% fewer context tokens than basic memory. The corrected implementation improves GEDAM LoCoMo recall from 0.205 to 0.410 and MRR from 0.180 to 0.262. Similarity remains the strongest positive-retrieval arm on recall, so the paper should describe GEDAM as a validity/context-control method rather than claim universal retrieval superiority.

## Explicit validity and abstention suite

The separate 26-case labeled safety suite measures answer recall, false abstention, no-answer false positives, correct abstention, and conflict detection.

| Method | Answer recall | False abstention | No-answer FP | Correct abstention | Conflict detection recall |
|---|---:|---:|---:|---:|---:|
| No memory | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| Basic memory | 0.769 | 0.154 | 0.846 | 0.154 | 0.000 |
| Similarity | 0.769 | 0.154 | 0.846 | 0.154 | 0.000 |
| **GEDAM v3** | **0.615** | **0.308** | **0.692** | **0.308** | **1.000** |

The safety suite shows GEDAM detects all labeled conflicts and lowers no-answer false positives relative to basic/similarity retrieval, while still losing some answer recall. These metrics are labeled synthetic-policy results and should be reported separately from LoCoMo.

## Token accounting

Context tokens are exact rendered-packet counts, not estimates. Source context averages 21,221.6 tokens. GEDAM averages 442.8 retrieved-context tokens, compared with 501.0 for basic memory and 126.5 for lexical similarity. Provider billing tokens and generated-answer tokens require a separate pinned-model generation study and are not inferred here.
