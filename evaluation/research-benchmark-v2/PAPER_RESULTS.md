# Paper-ready benchmark results

We evaluated GEDAM on all 10 conversations and 1,986 question-answer items from LoCoMo. The comparison included no memory, full conversation history, a deterministic lexical similarity retriever, and the existing 0xMemory baseline. All retrieval systems received the same observation store and questions. Results use top-k=5 and exact `cl100k_base` tokenization.

| Method | Recall@5 | MRR | Precision@5 | Irrelevant rate | Context tokens | Compression |
|---|---:|---:|---:|---:|---:|---:|
| No memory | 0.000 | 0.000 | 0.000 | 0.000 | 0.0 | 100.0% |
| Full history | 0.804 | 0.031 | 0.004 | 0.996 | 21,221.6 | 0.0% |
| Similarity | 0.499 | 0.432 | 0.115 | 0.885 | 126.5 | 99.4% |
| Existing baseline | 0.298 | 0.263 | 0.072 | 0.713 | 381.4 | 98.2% |
| **GEDAM** | **0.205** | **0.180** | **0.141** | **0.327** | **133.6** | **99.3%** |

GEDAM reduced irrelevant retrieval by 38.2 percentage points relative to the existing baseline and by 55.7 points relative to lexical similarity. Its mean context was 65.0% smaller than the existing baseline and more than 99% smaller than full history. GEDAM’s precision was higher than both memory baselines, while its recall remained lower than lexical similarity; this trade-off is reported directly rather than converted into an unsupported overall win claim.

Paired conversation-cluster bootstrap intervals (4,000 draws, 95% CI) for GEDAM minus the existing baseline were: Recall@5 −0.090 [−0.108, −0.071], Precision@5 +0.067 [+0.049, +0.084], irrelevant rate −0.382 [−0.423, −0.341], and context tokens −245.3 [−267.4, −222.7].

LoCoMo does not contain deletion, expiry, no-answer, or contradiction labels. Therefore stale-hit rate, valid-memory suppression, no-answer false-positive rate, and conflict-resolution accuracy are not estimated from this dataset and require a separate temporal/negative benchmark.
