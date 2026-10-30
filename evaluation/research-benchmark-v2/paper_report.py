#!/usr/bin/env python3
"""Create a paper-facing report from a completed LoCoMo v2 run.

Uncertainty is clustered by conversation (the independent unit in LoCoMo),
not by QA item, using a fixed-seed paired bootstrap.
"""
from __future__ import annotations

import argparse, csv, json, random, statistics
from pathlib import Path

METRICS = {
    "recall_at_k": "Recall@k",
    "mrr": "MRR",
    "precision_at_k": "Precision@k",
    "evidence_recall_any": "Evidence recall-any",
    "irrelevant_rate": "Irrelevant retrieval rate",
    "answer_evidence_f1": "Answer-evidence F1",
    "context_tokens": "Context tokens",
    "compression_vs_full_history": "Compression vs full history",
}


def mean(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else 0.0


def bootstrap(rows, a, b, key, seed=20261030, n=4000):
    groups = sorted({r["sample_id"] for r in rows})
    # Collapse each conversation to a mean before resampling. This preserves
    # the intended cluster bootstrap while avoiding repeated scans of 10k rows.
    by = {}
    for g in groups:
        by[g] = {c: mean([r for r in rows if r["sample_id"] == g and r["condition"] == c], key) for c in (a, b)}
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        draw = [groups[rng.randrange(len(groups))] for _ in groups]
        diffs.append(sum(by[g][a] - by[g][b] for g in draw) / len(draw))
    diffs.sort()
    return statistics.mean(diffs), diffs[int(0.025*n)], diffs[int(0.975*n)-1]


def main():
    p = argparse.ArgumentParser(); p.add_argument("run", type=Path); p.add_argument("--output", type=Path, required=True); args = p.parse_args()
    report = json.loads((args.run / "results.json").read_text())
    rows = report["results"]
    summary = {c: [r for r in rows if r["condition"] == c] for c in report["conditions"]}
    lines = ["# Research benchmark report: GEDAM memory layer", "", "## Protocol", "", f"Dataset: LoCoMo (`{report['dataset']}`), SHA-256 `{report['dataset_sha256']}`; {report['conversation_count']} conversations and {report['qa_count']} QA items; top-k={report['limit']}; tokenizer=`{report['tokenizer']}`.", "", "The five arms are no-memory, full-history, deterministic lexical similarity, the existing 0xMemory baseline ranker, and GEDAM. Full-history is a context/quality ceiling; no-memory is the empty-context control. All retrieval arms see the same observation corpus and the same question; no QA answers are used for ranking.", "", "## Aggregate metrics", "", "| Arm | Recall@k | MRR | Precision@k | Evidence recall-any | Irrelevant rate | Answer-evidence F1 | Context tokens | Compression |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for c in report["conditions"]:
        r = summary[c]
        lines.append(f"| {c} | {mean(r,'recall_at_k'):.3f} | {mean(r,'mrr'):.3f} | {mean(r,'precision_at_k'):.3f} | {mean(r,'evidence_recall_any'):.3f} | {mean(r,'irrelevant_rate'):.3f} | {mean(r,'answer_evidence_f1'):.3f} | {mean(r,'context_tokens'):.1f} | {mean(r,'compression_vs_full_history'):.1%} |")
    lines += ["", "## Paired clustered bootstrap", "", "Differences are GEDAM minus the comparison arm. The 95% interval resamples the 10 conversation IDs, preserving within-conversation dependence (seed 20261030; 4,000 draws).", "", "| Metric | vs similarity | vs baseline | vs full history |", "| --- | --- | --- | --- |"]
    for key, label in METRICS.items():
        cells=[]
        for other in ("similarity", "baseline", "full_history"):
            m, lo, hi = bootstrap(rows, "gedam", other, key)
            cells.append(f"{m:+.3f} [{lo:+.3f}, {hi:+.3f}]")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines += ["", "## Memory-safety metrics", "", "| Metric | LoCoMo status | Why |", "| --- | --- | --- |", "| Stale-hit rate | N/A | LoCoMo has no deletion/expiry labels. |", "| Valid-memory suppression | N/A | LoCoMo has no explicit valid-memory suppression cases. |", "| No-answer false-positive rate | N/A | LoCoMo QA is answer-bearing and has no abstention labels. |", "| Conflict resolution accuracy | N/A | LoCoMo does not label contradictory memory pairs. |", "| Retrieval recall / precision / irrelevant rate | Measured | Evidence IDs provide question-level relevance labels. |", "", "## Token and context accounting", "", "Context tokens are exact counts of the rendered retrieval packet using the tokenizer above. Source tokens are the full dialogue count, and compression is `1 - context_tokens/source_tokens`. Provider billing counters and generated-answer tokens are deliberately not inferred from context length; they require a separate answer-generation run with a pinned provider/model and logged usage fields.", "", "## Reproducibility and limits", "", "- Raw per-question rows: `run/results.json`; aggregate CSV: `run/summary.csv`.", "- Answer-evidence F1 is a support proxy between the gold answer string and rendered context, not free-form answer correctness.", "- Similarity is a deterministic lexical retriever, not a claim about a third-party commercial system.", "- LoCoMo is the positive evidence benchmark. A separate temporal/negative suite is required for stale-memory, suppression, abstention, and conflict claims.", ""]
    args.output.write_text("\n".join(lines))


if __name__ == "__main__": main()
