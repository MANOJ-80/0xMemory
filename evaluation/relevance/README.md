# Experimental relevance gate: calibration and independent reserved cases

For Ubuntu installation and Bash reproduction commands, follow [Ubuntu setup](../../UBUNTU_SETUP.md#14-optional-editor-handoff-dashboard-and-evaluation). Record Linux results separately from the committed Windows artifacts.

## Outcome and release decision

This report records a historical cosine-gate experiment on the earlier
retrieval configuration; the stored results do not represent the current EDAM
defaults or the current expanded evaluation runner. In that experiment, cosine
gating did not improve no-answer behavior on its reserved partition. Keep those
artifacts as historical evidence and use fresh output directories for the EDAM
policy and dataset.

| Partition | Answerable / unanswered | Ungated answer recall | Gated answer recall | Ungated no-answer false positives | Gated no-answer false positives |
| --- | --- | ---: | ---: | ---: | ---: |
| Development | 4 / 4 | 4/4 | 4/4 | 4/4 | 2/4 |
| Newly reserved | 8 / 8 | 8/8 | 8/8 | 8/8 | 8/8 |

False abstention on answerable cases was zero in both partitions. The remaining
unanswered questions have related vocabulary but missing information: approval,
ownership, contract terms, reasons, budgets, and contact details. For example,
“RabbitMQ is the message broker” does not answer why the team selected it.

## Method

The 24 questions were authored and split before calibration: eight development
cases and 16 new reserved cases. None is a query copied from the earlier 30-case
lifecycle dataset. Both partitions are balanced between answerable and unanswered
questions. They remain assistant-authored synthetic cases, not independently
reviewed real-user questions. Every memory in this study is active, isolating
relevance from lifecycle state.

Each query corpus has two distractors and, for answerable cases, one relevant
memory. With k=5 the ungated mode returns the entire tiny corpus, so its 100%
answer recall is expected by construction, not evidence of strong ranking.
This study tests retention/abstention behavior, not ranking quality at scale.

The runner builds real Chroma collections and queries actual all-MiniLM-L6-v2
embeddings. It computes cosine similarity from the query and stored embedding,
including their norms; it does not equate Chroma distance or a reciprocal-rank
fusion score with calibrated confidence. Both variants receive identical semantic
candidates and production hybrid ranking. Only relevance eligibility differs.

Cosine similarity is a relatedness signal, not proof that a statement answers the
question. See [Sentence Transformers similarity documentation](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html).
The embedding API supports normalized and unnormalized outputs, so the implementation
explicitly normalizes the dot product mathematically rather than assuming unit
vectors. [Encoder reference](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html).

The predeclared threshold grid was 0.25 through 0.75 in steps of 0.05. Selection
minimized `2 * (1 - answer_recall) + no_answer_false_positive_rate`; ties chose
the lower threshold to preserve recall. On development data the chosen threshold
was **0.25**. This policy was written to disk before the reserved evaluation and
was not changed after seeing those results. Higher development thresholds reduced
false positives but also hid useful memories; all trials are retained in
[policy.json](development/policy.json).

Dataset SHA-256:
`2e0ef6e1b992e0bc939bcbaf1124ad21e0b3c74ad1e2cff2d0372e0aae2a5273`

Raw candidate cosine scores, returned IDs, relevance labels, failures, and the
frozen policy are preserved in [development results](development/results.json)
and [reserved results](held-out/results.json). Generated summaries are available
in [development report](development/REPORT.md) and [reserved report](held-out/REPORT.md).

A separate [real MCP smoke check](mcp-smoke.json) enabled the project gate and
confirmed that an unrelated ocean question produced `no_relevant_memory`, while
a logging-format question retained its stored answer. It uses the actual MCP SDK
and server with ordinary subprocess pipes. This simple success does not override
the hard-negative failures in the reserved experiment.

## Experimental configuration

For the earlier cosine-only baseline experiment, a test project's
`.0xmemory/config.yaml` could merge this section without replacing other
settings, then restart its MCP server:

```yaml
retrieval:
  relevance_gate: true
  min_similarity: 0.25
```

The current `RetrievalConfig` defaults to EDAM with `relevance_gate: true`.
Select `architecture: baseline` to reproduce RRF-oriented ranking. Thresholds
are configured per project and must be calibrated on development data for that
embedding model and task distribution.

Python callers can explicitly use
`store.recall_context(query, relevance_gate=True, min_similarity=0.25)`.
The MCP and dashboard paths honor the project configuration through MemoryStore.
With embeddings unavailable, the gate requires overlap with at least half of
the non-stopword query tokens. This fallback is a heuristic and was unit-tested,
not measured as a replacement for the semantic experiment. File hints cannot
bypass the gate. Lifecycle filtering remains active independently.

Empty recall now includes `abstained` and `abstention_reason`: either
`no_relevant_memory` or `context_budget`. The MCP message distinguishes them.
This means no eligible memory was returned; it does not prove the answer does
not exist elsewhere. History queries remain subject to relevance when enabled;
use `list` for a full audit.

## Reproduce

After preparing the cached model, run from the engine root in PowerShell:

```powershell
$env:PYTHONUTF8='1'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.\.venv\Scripts\python.exe -m oxmemory.relevance_evaluation --phase calibrate --output evaluation/relevance/repeat-development
.\.venv\Scripts\python.exe -m oxmemory.relevance_evaluation --phase test --policy evaluation/relevance/repeat-development/policy.json --output evaluation/relevance/repeat-test
```

Choose fresh output directories. The test phase checks the policy dataset hash
and does not optimize thresholds. Model/index failures stop the run. The reserved
set is now inspected, so future relevance improvements require new reserved cases.

## What remains unresolved

Reliable answerability needs more than a cosine cutoff. A future reranker or
entailment/answerability model should be evaluated with hard negatives and paraphrases,
including cases where a fact is related but the requested attribute is missing.
It must be tested for false abstention as well as irrelevant retrieval. This work
does not implement or claim a solved answerability classifier.
