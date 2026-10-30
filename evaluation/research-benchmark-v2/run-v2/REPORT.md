# LoCoMo research benchmark: GEDAM versus memory baselines

Dataset: `locomo10.json` (SHA-256 `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4`).
Conversations: 10; QA items: 1986; top-k: 5; tokenizer: `cl100k_base`.

| Condition | n | Recall@k | MRR | Precision@k | Evidence recall-any | Irrelevant rate | Answer evidence F1 | Mean context tokens | Median context tokens | Mean source tokens | Compression vs full history |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_memory | 1986 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 0.0 | 21221.6 | 100.000% |
| full_history | 1986 | 0.804 | 0.031 | 0.004 | 0.840 | 0.996 | 0.000 | 21221.6 | 22121.0 | 21221.6 | 0.000% |
| similarity | 1986 | 0.499 | 0.432 | 0.115 | 0.549 | 0.885 | 0.028 | 126.5 | 128.0 | 21221.6 | 99.388% |
| baseline | 1986 | 0.298 | 0.263 | 0.072 | 0.338 | 0.713 | 0.006 | 381.4 | 496.0 | 21221.6 | 98.154% |
| gedam | 1986 | 0.205 | 0.180 | 0.141 | 0.232 | 0.327 | 0.010 | 133.6 | 0.0 | 21221.6 | 99.340% |

## Conditions

- `no_memory`: empty context control.
- `full_history`: all dialogue turns; quality and compression reference.
- `similarity`: deterministic lexical TF-IDF-like observation retriever.
- `baseline`: 0xMemory existing baseline ranker with lifecycle/relevance safeguards disabled.
- `gedam`: 0xMemory GEDAM ranker with relevance gate and adaptive packing.

## Reproducibility

Raw per-question rows are in `results.json`; aggregate CSV is `summary.csv`. The source dataset is the authors' LoCoMo release and is cited in the report metadata.

## Limits

- LoCoMo provides evidence IDs but does not provide stale/deletion labels; stale-hit and valid-memory-suppression require a separate temporal/negative benchmark.
- Answer evidence F1 measures support in the retrieved packet, not free-form LLM answer correctness.
- Similarity is a deterministic lexical TF-IDF-like retriever, not an external vendor product.
- Provider token/cost usage requires an answer-generation run; context counts here are exact rendered-payload counts.
