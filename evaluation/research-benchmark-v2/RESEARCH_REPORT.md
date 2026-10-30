# Research benchmark report: GEDAM memory layer

## Protocol

Dataset: LoCoMo (`locomo10.json`), SHA-256 `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`; 10 conversations and 1986 QA items; top-k=5; tokenizer=`cl100k_base`.

The five arms are no-memory, full-history, deterministic lexical similarity, the existing 0xMemory baseline ranker, and GEDAM. Full-history is a context/quality ceiling; no-memory is the empty-context control. All retrieval arms see the same observation corpus and the same question; no QA answers are used for ranking.

## Aggregate metrics

| Arm | Recall@k | MRR | Precision@k | Evidence recall-any | Irrelevant rate | Answer-evidence F1 | Context tokens | Compression |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 100.0% |
| full_history | 0.804 | 0.031 | 0.004 | 0.840 | 0.996 | 0.000 | 21221.6 | 0.0% |
| similarity | 0.499 | 0.432 | 0.115 | 0.549 | 0.885 | 0.028 | 126.5 | 99.4% |
| baseline | 0.298 | 0.263 | 0.072 | 0.338 | 0.713 | 0.006 | 381.4 | 98.2% |
| gedam | 0.205 | 0.180 | 0.141 | 0.232 | 0.327 | 0.010 | 133.6 | 99.3% |

## Paired clustered bootstrap

Differences are GEDAM minus the comparison arm. The 95% interval resamples the 10 conversation IDs, preserving within-conversation dependence (seed 20261030; 4,000 draws).

| Metric | vs similarity | vs baseline | vs full history |
| --- | --- | --- | --- |
| Recall@k | -0.295 [-0.313, -0.275] | -0.093 [-0.109, -0.077] | -0.600 [-0.638, -0.561] |
| MRR | -0.253 [-0.265, -0.241] | -0.083 [-0.097, -0.067] | +0.148 [+0.126, +0.169] |
| Precision@k | +0.025 [+0.005, +0.043] | +0.068 [+0.049, +0.085] | +0.136 [+0.114, +0.156] |
| Evidence recall-any | -0.318 [-0.341, -0.293] | -0.106 [-0.127, -0.084] | -0.609 [-0.648, -0.572] |
| Irrelevant retrieval rate | -0.558 [-0.589, -0.527] | -0.385 [-0.424, -0.346] | -0.669 [-0.702, -0.634] |
| Answer-evidence F1 | -0.018 [-0.020, -0.016] | +0.003 [+0.002, +0.005] | +0.009 [+0.008, +0.011] |
| Context tokens | +7.021 [-9.142, +24.078] | -247.660 [-268.202, -226.889] | -21075.397 [-22782.748, -19081.978] |
| Compression vs full history | -0.000 [-0.002, +0.000] | +0.012 [+0.011, +0.013] | +0.993 [+0.992, +0.995] |

## Memory-safety metrics

| Metric | LoCoMo status | Why |
| --- | --- | --- |
| Stale-hit rate | N/A | LoCoMo has no deletion/expiry labels. |
| Valid-memory suppression | N/A | LoCoMo has no explicit valid-memory suppression cases. |
| No-answer false-positive rate | N/A | LoCoMo QA is answer-bearing and has no abstention labels. |
| Conflict resolution accuracy | N/A | LoCoMo does not label contradictory memory pairs. |
| Retrieval recall / precision / irrelevant rate | Measured | Evidence IDs provide question-level relevance labels. |

## Token and context accounting

Context tokens are exact counts of the rendered retrieval packet using the tokenizer above. Source tokens are the full dialogue count, and compression is `1 - context_tokens/source_tokens`. Provider billing counters and generated-answer tokens are deliberately not inferred from context length; they require a separate answer-generation run with a pinned provider/model and logged usage fields.

## Reproducibility and limits

- Raw per-question rows: `run/results.json`; aggregate CSV: `run/summary.csv`.
- Answer-evidence F1 is a support proxy between the gold answer string and rendered context, not free-form answer correctness.
- Similarity is a deterministic lexical retriever, not a claim about a third-party commercial system.
- LoCoMo is the positive evidence benchmark. A separate temporal/negative suite is required for stale-memory, suppression, abstention, and conflict claims.
