# Findings from the first controlled lifecycle experiment

Run date: 2026-10-07. Real all-MiniLM-L6-v2 embeddings, ChromaDB 1.5.9,
sentence-transformers 6.1.0, Python 3.12.0 on Windows.

The dataset was fixed before semantic execution. Both run folders contain the same
dataset SHA-256:

`3731d6d9cd33e33ff01af0e75c829441e501bf48b46bf8990e71a60ccd0336c9`

Five development scenarios were executed first; the remaining 25 scenarios were
then evaluated without ranking/threshold changes. Labels are assistant-authored
and still need human review. These results demonstrate a controlled mechanism on
small synthetic fixtures, not general research superiority.

## Main results: reserved partition only

There are **25 scenarios, 30 checkpoints, and 60 variant outputs** in this partition.
Five still-valid scenarios each contribute a pending-review and a reviewed checkpoint.
The rows below have different denominators; do not average these percentages together.

| Measurement | Basic filtering-disabled ablation | Lifecycle filtering | Denominator |
| --- | ---: | ---: | --- |
| Queries returning factually outdated memory | 12/12 (100%) | 0/12 (0%) | 7 changed + 5 superseded scenarios |
| Queries returning any stale/superseded entry | 17/17 (100%) | 0/17 (0%) | Above 12 + 5 pending-review checkpoints |
| Recall@5 over stored true answers | 20/20 (100%) | 15/20 (75%) | 20 answerable checkpoints; one relevant memory each |
| MRR over stored true answers | 1.00 | 0.75 | Same 20 checkpoints |
| Replacement retrieved without outdated decision | 0/5 (0%) | 5/5 (100%) | Reviewed supersession cases |
| Unrelated-change relevant decision retained | 5/5 (100%) | 5/5 (100%) | Unrelated-change cases |
| Still-true memory retrieved while awaiting review | 5/5 (100%) | 0/5 (0%) | Pending verification after linked-file refactors |
| Still-true memory retrieved after verification | 5/5 (100%) | 5/5 (100%) | Same five refactors after explicit review |
| Content returned when no stored answer exists | 10/10 (100%) | 10/10 (100%) | 7 not-yet-recorded replacements + 3 unrelated questions |

![Reserved partition descriptive chart](held-out/charts/held_out.svg)

## What improved

Lifecycle filtering excluded every outdated labelled entry in these fixtures.
Supersession preserved the historical record while preventing its return as active
advice. Unrelated changes did not remove relevant decisions. The comparison uses
the same hybrid ranking and semantic candidates, so it isolates lifecycle eligibility
rather than comparing two different search algorithms.

This outcome is consistent with the implemented filter's intended behavior. A zero
outdated-hit result here does not establish automatic truth detection: the fixtures
provide evidence links, explicit observation, and correct review/replacement actions.
Unlinked memories and unobserved changes are outside this result.

## Tradeoff: less context while verification is pending

In five refactor scenarios, the linked file changed but its factual setting did not.
Observation marked the decision stale. Its label remained relevant because it was
still true; lifecycle filtering withheld it, reducing overall recall from 100% to
75% across the 20 answerable checkpoints. After explicit verification, retrieval
recovered in all five scenarios.

This is a visible safety/availability tradeoff. Report the pending-review loss with
the stale-filtering benefit; do not relabel stale-but-true entries as irrelevant to
hide it. A later interface could make pending review more visible without presenting
unverified content as current guidance.

## Unresolved failure: no-answer retrieval

Both modes returned active distractors when no stored memory answered the question.
Filtering removes obsolete context but has no semantic relevance threshold. Nearest
neighbors are still returned even when none is a good answer. The three explicit
unrelated-question cases failed 3/3; the seven changed-but-not-yet-replaced cases
also returned distractors after the original was filtered.

Therefore “the system never returns irrelevant information” is not supported.
Nor does returning content prove an LLM would hallucinate: this experiment does not
generate answers. A separate relevance gate or abstention policy needs development
and a new reserved test set. Do not tune a threshold on these inspected cases and
reuse their score as untouched test performance.

## Appropriate wording for a project report

> We evaluated lifecycle-aware retrieval using 30 synthetic Git-backed scenarios,
> partitioned into five development and 25 reserved scenarios. In the reserved
> partition, enabling lifecycle filtering reduced queries returning labelled
> outdated memories from 12/12 to 0/12. It also withheld five still-valid memories
> pending verification; retrieval recovered after review. Both variants returned
> content in all ten checkpoints with no stored answer, exposing an unresolved
> abstention limitation. These results assess retrieval behavior under supplied
> evidence and review actions, not autonomous truth verification or coding success.

## Reproduction and audit

See [README.md](README.md) for commands and metric definitions. Inspect
[raw results](held-out/results.json), [summary CSV](held-out/summary.csv), and
[generated report](held-out/REPORT.md) for per-query results and recorded failures.
Real Git diffs and lifecycle responses are included in the audit even though the
temporary fixture repositories are removed after their stores close.

The source revision field points to the preceding committed handoff revision;
dirty status and evaluator source hashes identify that this first experiment ran
with new local evaluator files. Matching source snapshots are retained under
`source/` in each run. Subsequent formatting and portable output serialization
changes do not change the dataset, ranking, or recorded measurements. Dataset
contents are frozen in each run folder with canonical UTF-8/LF line endings.
Publishing the new evaluator and results together is still necessary for another
person to reproduce this exact version from GitHub.

No deployment, external agent call, live Dodo change, or push occurred during this
experiment. The original project's memories and the successful Dodo demo are intact.
