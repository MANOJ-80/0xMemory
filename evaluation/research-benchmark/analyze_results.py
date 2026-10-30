#!/usr/bin/env python3
"""Create research tables from an immutable oxmemory benchmark run.

The source benchmark reports lifecycle/retrieval outcomes and a conservative
bytes/3 context estimate.  This analysis adds an exact tokenizer count for the
rendered memory payloads and a fair full-history compression reference.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

try:
    import tiktoken
except ImportError:  # pragma: no cover - the report records the fallback
    tiktoken = None


def tokenizer():
    if tiktoken is None:
        return None, "utf8_bytes_div_3"
    try:
        return tiktoken.get_encoding("cl100k_base"), "cl100k_base"
    except Exception:
        return None, "utf8_bytes_div_3"


def count(text: str, enc) -> int:
    if enc is None:
        return (len(text.encode("utf-8")) + 2) // 3
    return len(enc.encode(text))


def memory_block(memory: dict) -> str:
    return (
        f"Memory record [{memory.get('id', 'unknown')}]\n"
        f"Claim: {memory.get('content', '')}\n"
        f"Status: {memory.get('status', 'unknown')}\n"
    )


def full_history(audit: dict) -> str:
    return "\n".join(memory_block(m) for m in audit.get("memories", []))


def exact_packed(row: dict, enc) -> int:
    return count("\n".join(memory_block(m) for m in row.get("retrieved", [])), enc)


def mean(values):
    return statistics.mean(values) if values else None


def pct(n, d):
    return None if not d else n / d


def summarize(report: dict, source: Path) -> dict:
    enc, tokenizer_name = tokenizer()
    rows = report["results"]
    audits = {(a["scenario"], a["changed_commit"]): a for a in report["audits"]}
    audit_by_scenario = {a["scenario"]: a for a in report["audits"]}
    full_tokens = {sid: count(full_history(a), enc) for sid, a in audit_by_scenario.items()}

    for row in rows:
        row["exact_packed_context_tokens"] = exact_packed(row, enc)
        row["full_history_tokens"] = full_tokens.get(row["scenario"], 0)
        row["context_reduction_vs_full_history"] = (
            1 - row["exact_packed_context_tokens"] / row["full_history_tokens"]
            if row["full_history_tokens"] else None
        )
        row["exact_context_estimate_error"] = (
            row["exact_packed_context_tokens"] - row.get("context_tokens", 0)
        )

    groups = []
    for category in ["all", *sorted({r["category"] for r in rows})]:
        for variant in ["no_memory", "basic", "current", "edam", "full_history"]:
            selected = [r for r in rows if category == "all" or r["category"] == category]
            if variant == "full_history":
                selected = selected[::4]  # one checkpoint per scenario, avoid fourfold duplication
            else:
                selected = [r for r in selected if r["variant"] == variant]
            metric_rows = [r.get("metrics", {}) for r in selected]
            def avg(key):
                vals = [m[key] for m in metric_rows if m.get(key) is not None]
                return mean(vals)
            context = ([r["full_history_tokens"] for r in selected] if variant == "full_history"
                       else [r["exact_packed_context_tokens"] for r in selected])
            groups.append({
                "category": category, "variant": variant, "n": len(selected),
                "recall_at_k": avg("recall_at_k"),
                "mrr": avg("reciprocal_rank"),
                "budgeted_recall": avg("budgeted_recall"),
                "outdated_hit": avg("outdated_hit"),
                "outdated_rate": avg("outdated_memory_retrieval_rate"),
                "valid_suppression": avg("valid_memory_suppression_rate"),
                "no_answer_false_positive": avg("no_answer_false_positive"),
                "update_correct": avg("update_correct"),
                "evidence_state_correct": avg("evidence_state_correct"),
                "mean_exact_context_tokens": mean(context),
                "median_exact_context_tokens": statistics.median(context) if context else None,
                "mean_context_bytes": mean([r.get("context_bytes", 0) for r in selected]) if selected and variant != "full_history" else None,
            })

    paired = []
    by_key = defaultdict(dict)
    for r in rows:
        by_key[(r["scenario"], r["checkpoint"])][r["variant"]] = r
    for key, arms in sorted(by_key.items()):
        if "edam" not in arms:
            continue
        edam = arms["edam"]
        full = edam["full_history_tokens"]
        packed = edam["exact_packed_context_tokens"]
        paired.append({
            "scenario": key[0], "checkpoint": key[1],
            "edam_context_tokens": packed, "full_history_tokens": full,
            "reduction": 1 - packed / full if full else None,
            "edam_recall": edam["metrics"].get("recall_at_k"),
            "edam_outdated_hit": edam["metrics"].get("outdated_hit"),
            "edam_valid_suppression": edam["metrics"].get("valid_memory_suppression_rate"),
        })

    output = {
        "analysis": "research_benchmark_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "source_results": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "tokenizer": tokenizer_name,
        "tokenizer_note": "Exact rendered-memory payload count with cl100k_base; not provider-reported full prompt usage.",
        "conditions": [
            {"name": "no_memory", "description": "No persistent memory payload."},
            {"name": "basic", "description": "Existing baseline retrieval with lifecycle filtering disabled."},
            {"name": "current", "description": "Existing lifecycle-aware baseline ranker."},
            {"name": "edam", "description": "GEDAM evidence-aware scoring, abstention and adaptive packing."},
            {"name": "full_history", "description": "All available memory records rendered as context; compression reference only."},
        ],
        "groups": groups,
        "paired": paired,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "limitations": [
            "The source fixtures are synthetic, though the held-out partition was fixed before the run.",
            "Full-history is a rendered-memory compression reference, not an agent transcript replay.",
            "Exact context counts cover the memory payload only; provider turn usage includes system, tools, repository reads and runtime overhead.",
            "No external memory product was installed. Basic/current are the project's existing retrieval baselines; external-product comparisons require pinned implementations and identical APIs.",
            "No claim of cost reduction is made from context payload counts; provider-reported usage must be collected in matched agent runs.",
        ],
    }
    return output


def write(out: Path, data: dict):
    out.mkdir(parents=True, exist_ok=False)
    (out / "analysis.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    with (out / "groups.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data["groups"][0]))
        writer.writeheader(); writer.writerows(data["groups"])
    with (out / "paired.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data["paired"][0]))
        writer.writeheader(); writer.writerows(data["paired"])
    lines = [
        "# Research benchmark analysis", "",
        f"Source: `{data['source_results']}`; source SHA-256: `{data['source_sha256']}`.",
        f"Exact memory-payload tokenizer: `{data['tokenizer']}`.", "",
        "This report compares the project baselines and GEDAM. `full_history` is a fair compression reference: it renders every available memory record for the same checkpoint. It is not a provider transcript replay. No-memory is a utility/safety control, not a compression baseline.", "",
        "## Main metrics", "",
        "| Slice | Condition | n | Recall@k | MRR | Budget recall | Outdated hit | Valid suppression | No-answer FP | Update correct | Mean exact context tokens | Median exact context tokens |", 
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    def fmt(x): return "N/A" if x is None else f"{x:.3f}"
    for g in data["groups"]:
        if g["category"] != "all": continue
        lines.append("| {category} | {variant} | {n} | {recall_at_k} | {mrr} | {budgeted_recall} | {outdated_hit} | {valid_suppression} | {no_answer_false_positive} | {update_correct} | {mean_exact_context_tokens} | {median_exact_context_tokens} |".format(category=g["category"],variant=g["variant"],n=g["n"],recall_at_k=fmt(g["recall_at_k"]),mrr=fmt(g["mrr"]),budgeted_recall=fmt(g["budgeted_recall"]),outdated_hit=fmt(g["outdated_hit"]),valid_suppression=fmt(g["valid_suppression"]),no_answer_false_positive=fmt(g["no_answer_false_positive"]),update_correct=fmt(g["update_correct"]),mean_exact_context_tokens=fmt(g["mean_exact_context_tokens"]),median_exact_context_tokens=fmt(g["median_exact_context_tokens"])))
    lines += ["", "## Interpretation rules", "", "- Report every numerator and denominator from `groups.csv`; N/A means the slice has no eligible denominator.", "- Compare token/context reduction against `full_history`, conditional on recall, stale-hit and answerability quality.", "- Use `pilot/raw-results.json` for Codex-reported setup/follow-up turn tokens; this retrieval benchmark does not invent provider costs.", "", "## Limitations", "", *[f"- {x}" for x in data["limitations"]], ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--source", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); write(args.output, summarize(json.loads(args.source.read_text()), args.source))


if __name__ == "__main__": main()
