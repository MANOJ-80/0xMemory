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
| baseline | 0.437 | 0.377 | 0.101 | 0.484 | 0.899 | 0.007 | 501.0 | 97.6% |
| gedam | 0.410 | 0.262 | 0.106 | 0.455 | 0.817 | 0.007 | 442.8 | 97.8% |

## Paired clustered bootstrap

Differences are GEDAM minus the comparison arm. The 95% interval resamples the 10 conversation IDs, preserving within-conversation dependence (seed 20261030; 4,000 draws).

| Metric | vs similarity | vs baseline | vs full history |
| --- | --- | --- | --- |
| Recall@k | -0.089 [-0.111, -0.069] | -0.026 [-0.039, -0.015] | -0.394 [-0.432, -0.358] |
| MRR | -0.170 [-0.194, -0.146] | -0.116 [-0.133, -0.099] | +0.229 [+0.212, +0.248] |
| Precision@k | -0.010 [-0.019, -0.001] | +0.005 [-0.000, +0.011] | +0.101 [+0.093, +0.108] |
| Evidence recall-any | -0.096 [-0.122, -0.073] | -0.028 [-0.041, -0.016] | -0.385 [-0.423, -0.350] |
| Irrelevant retrieval rate | -0.066 [-0.080, -0.053] | -0.081 [-0.092, -0.070] | -0.176 [-0.189, -0.163] |
| Answer-evidence F1 | -0.021 [-0.022, -0.019] | -0.000 [-0.001, +0.000] | +0.007 [+0.006, +0.007] |
| Context tokens | +317.719 [+310.274, +325.478] | -56.950 [-63.687, -49.647] | -20383.064 [-22461.795, -18004.728] |
| Compression vs full history | -0.016 [-0.019, -0.014] | +0.003 [+0.002, +0.003] | +0.978 [+0.974, +0.981] |

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
