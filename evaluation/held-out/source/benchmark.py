"""Controlled lifecycle ablation with real Git transitions and fixed synthetic labels.

python -m oxmemory.benchmark --output evaluation/development --partition development
python -m oxmemory.benchmark --output evaluation/held-out --partition held_out --semantic
"""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from types import SimpleNamespace

from oxmemory.benchmark_data import scenarios
from oxmemory.core.models import Memory, MemoryType
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore
from oxmemory.storage.repository import Repository
from oxmemory.storage.retrieval import rank_memories

VARIANTS = ("basic", "lifecycle")


def measure(ids, relevant, outdated, ineligible, replacement=None):
    """Truth labels are independent of stale/superseded lifecycle state."""
    ids, relevant, outdated, ineligible = list(ids), set(relevant), set(outdated), set(ineligible)
    return {
        "recall_at_k": len(set(ids) & relevant) / len(relevant) if relevant else None,
        "reciprocal_rank": next((1 / i for i, mid in enumerate(ids, 1) if mid in relevant), 0.0)
        if relevant else None,
        "outdated_hit": bool(set(ids) & outdated) if outdated else None,
        "outdated_fraction": len(set(ids) & outdated) / len(ids) if ids else 0.0,
        "ineligible_hit": bool(set(ids) & ineligible) if ineligible else None,
        "no_answer_false_positive": bool(ids) if not relevant else None,
        "update_correct": replacement in ids and not (set(ids) & outdated)
        if replacement else None,
    }


def aggregate(rows):
    """Macro averages with explicit denominators; never convert N/A into zero."""
    groups = []
    for partition in sorted({r["partition"] for r in rows}):
        subset = [r for r in rows if r["partition"] == partition]
        for category in ["all", *sorted({r["category"] for r in subset})]:
            for variant in VARIANTS:
                selected = [r for r in subset if r["variant"] == variant
                            and (category == "all" or r["category"] == category)]
                group = dict(partition=partition, category=category, variant=variant,
                             checkpoints=len(selected))
                for metric in selected[0]["metrics"]:
                    values = [r["metrics"][metric] for r in selected
                              if r["metrics"][metric] is not None]
                    group[metric] = sum(values) / len(values) if values else None
                    group[metric + "_n"] = len(values)
                groups.append(group)
    return groups


def git(root, *args):
    executable = shutil.which("git") or "C:/Program Files/Git/cmd/git.exe"
    env = dict(os.environ, GIT_AUTHOR_DATE="2026-01-01T00:00:00+00:00",
               GIT_COMMITTER_DATE="2026-01-01T00:00:00+00:00")
    result = subprocess.run(
        [executable, "-C", str(root), "-c", "user.name=Benchmark",
         "-c", "user.email=benchmark@example.invalid", "-c", "commit.gpgsign=false",
         "-c", "core.hooksPath=", *args], env=env, capture_output=True,
        text=True, encoding="utf-8", timeout=30, check=True,
    )
    return result.stdout.strip()


def commit(root, files, message):
    git(root, "add", "--", *files)
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


def collect(store, fixture, roles, checkpoint, vector, limit):
    memories = store.markdown.get_all_memories()
    candidates = []
    if vector is not None:
        # Index/query outside rank_memories: its production fallback must never
        # silently turn a semantic experiment into a keyword experiment.
        for memory in memories:
            vector.upsert(memory)
        if vector.count() != len(memories):
            raise RuntimeError("Incomplete semantic index")
        candidates = vector.search(fixture["query"], limit=len(memories))
        if {r["id"] for r in candidates} != {m.id for m in memories}:
            raise RuntimeError("Semantic query did not return the complete candidate corpus")

    # Both variants receive exactly the same real semantic candidate ranking.
    proxy = SimpleNamespace(markdown=store.markdown,
                            vector_store=SimpleNamespace(search=lambda *a, **k: candidates))
    relevant = {roles[role] for role in fixture["relevant_roles"]}
    outdated = {roles[role] for role in fixture["outdated_roles"]}
    ineligible = {m.id for m in memories if m.status.value != "active"}
    distance = {r["id"]: r["distance"] for r in candidates}
    rows = []
    for variant in VARIANTS:
        ranked = rank_memories(
            proxy, fixture["query"], limit, None, vector is not None,
            [fixture["file_hint"]] if fixture["file_hint"] else [], [],
            include_history=variant == "basic",
        )
        ids = [r["memory"].id for r in ranked]
        rows.append(dict(
            scenario=fixture["id"], partition=fixture["partition"], category=fixture["category"],
            checkpoint=checkpoint, variant=variant, query=fixture["query"],
            file_hint=fixture["file_hint"], relevant_ids=sorted(relevant),
            outdated_ids=sorted(outdated), ineligible_ids=sorted(ineligible),
            retrieved=[dict(id=r["memory"].id, content=r["memory"].content,
                            status=r["memory"].status.value, score=r["score"],
                            reasons=r["reasons"], semantic_distance=distance.get(r["memory"].id),
                            commit=r["memory"].commit_sha) for r in ranked],
            metrics=measure(ids, relevant, outdated, ineligible, roles.get("replacement")),
        ))
    return rows


def run_scenario(fixture, distractors, model, semantic, limit):
    with tempfile.TemporaryDirectory(prefix="oxmemory-benchmark-") as tmp:
        root = Path(tmp)
        git(root, "init", "-q")
        evidence = root / fixture["file"]
        initial = f'{fixture["setting"]} = {fixture["before"]!r}\n'
        evidence.write_text(initial, encoding="utf-8")
        (root / "other.py").write_text("VERSION = 1\n", encoding="utf-8")
        initial_sha = commit(root, [fixture["file"], "other.py"], "Initial evidence")
        MarkdownManager(root).initialize_brain("Synthetic lifecycle benchmark")
        vector = None
        with MemoryStore(root, enable_vectors=False) as store:
            # Stable fixture IDs avoid UUID-based tie-breaking differences across runs.
            old = Memory(id="original", content=fixture["original"], type=MemoryType.DECISION,
                         file_paths=[fixture["file"]], commit_sha=initial_sha)
            Repository(root).validate_evidence(initial_sha, old.file_paths)
            store.markdown.add_memory(old)
            for index, content in enumerate(distractors):
                store.markdown.add_memory(Memory(id=f"noise-{index}", content=content))
            roles = {"original": old.id}
            if semantic:
                from oxmemory.storage.vector_store import VectorStore
                vector = VectorStore(root)
                vector._embedder = model  # One real model instance, no repeated weight loading.
            try:
                category = fixture["category"]
                changed_file = fixture["file"]
                if category in {"unrelated", "no_answer"}:
                    changed_file = "other.py"
                    after = "VERSION = 2\n"
                elif category == "valid":
                    after = initial + "\n# Refactor helper; configured policy is unchanged.\ndef configured_value():\n    return " + fixture["setting"] + "\n"
                else:
                    after = f'{fixture["setting"]} = {fixture["after"]!r}\n'
                (root / changed_file).write_text(after, encoding="utf-8")
                changed_sha = commit(root, [changed_file], "Change implementation")
                observation = store.observe_commit(changed_sha)
                events = [dict(operation="observe_commit", result=observation)]
                rows = []
                if category == "valid":
                    rows.extend(collect(store, fixture, roles, "pending_review", vector, limit))
                    reviewed = store.verify(old.id, changed_sha, "Fixture review: setting is unchanged; only a helper was added.")
                    events.append(dict(operation="verify", memory=reviewed.model_dump(mode="json")))
                elif category == "superseded":
                    replacement = store.supersede(old.id, fixture["replacement"], changed_sha,
                                                  "Fixture review: the setting now matches the replacement claim.")
                    roles["replacement"] = replacement.id
                    events.append(dict(operation="supersede", memory=replacement.model_dump(mode="json")))
                rows.extend(collect(store, fixture, roles, "after_review" if category in {"valid", "superseded"}
                                    else "after_observation", vector, limit))
                audit = dict(scenario=fixture["id"], initial_commit=initial_sha,
                             changed_commit=changed_sha, initial_file=fixture["file"],
                             initial_code=initial, changed_file=changed_file, changed_code=after,
                             diff=git(root, "diff", initial_sha, changed_sha, "--"), events=events,
                             memories=[m.model_dump(mode="json") for m in store.markdown.get_all_memories()])
                return rows, audit
            finally:
                if vector is not None:
                    vector.close()


def charts(summary, target, limit):
    """Portable SVG descriptive bars; no network renderer or statistical intervals."""
    target.mkdir()
    metrics = [("outdated_hit", "Queries returning outdated memory (lower is better)"),
               ("recall_at_k", f"Recall@{limit} on answerable checkpoints (higher is better)"),
               ("no_answer_false_positive", "Unanswerable queries returning content (lower is better)"),
               ("update_correct", "Replacement retrieved without outdated decision (higher is better)")]
    for partition in sorted({r["partition"] for r in summary}):
        grouped = {r["variant"]: r for r in summary
                   if r["partition"] == partition and r["category"] == "all"}
        elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="580" viewBox="0 0 960 580">',
                    '<rect width="960" height="580" fill="white"/>',
                    f'<text x="24" y="32" font-family="sans-serif" font-size="22">Synthetic lifecycle ablation: {escape(partition)}</text>']
        for index, (metric, title) in enumerate(metrics):
            top = 75 + index * 120
            elements.append(f'<text x="24" y="{top}" font-family="sans-serif" font-size="16">{escape(title)}</text>')
            for offset, variant in enumerate(VARIANTS):
                value = grouped[variant][metric]
                y = top + 12 + offset * 30
                color = "#9467bd" if variant == "basic" else "#16826b"
                label = "N/A" if value is None else f'{value:.1%} (n={grouped[variant][metric + "_n"]})'
                elements.extend([
                    f'<text x="24" y="{y+17}" font-family="sans-serif" font-size="14">{variant}</text>',
                    f'<rect x="130" y="{y}" width="600" height="22" fill="#eeeeee"/>',
                    f'<rect x="130" y="{y}" width="{600*(value or 0):.2f}" height="22" fill="{color}"/>',
                    f'<text x="750" y="{y+17}" font-family="sans-serif" font-size="14">{label}</text>',
                ])
        elements.append('<text x="24" y="566" font-family="sans-serif" font-size="12">Bars span 0–100%. Descriptive synthetic results; no confidence intervals or coding-success claims.</text></svg>')
        (target / f"{partition}.svg").write_text("\n".join(elements), encoding="utf-8")


def write_report(report, output):
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report["summary"][0]))
        writer.writeheader()
        writer.writerows(report["summary"])
    lines = ["# Synthetic commit-aware retrieval experiment", "",
             f'Mode: **{report["mode"]}**. Dataset SHA-256: `{report["dataset_sha256"]}`.', "",
             "Both variants use the same corpus, query, file hints, hybrid ranking, and semantic candidates.",
             "Only `include_history` differs. Basic is a controlled ablation, not a reproduction of an older release.", "",
             "| Partition/category | Variant | Checkpoints | Recall@k | MRR | Outdated hit | No-answer FP | Update correct |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    def fmt(value):
        return "N/A" if value is None else f"{value:.3f}"
    for group in report["summary"]:
        lines.append(f'| {group["partition"]}/{group["category"]} | {group["variant"]} | {group["checkpoints"]} | '
                     + " | ".join(fmt(group[m]) for m in ["recall_at_k", "reciprocal_rank", "outdated_hit",
                                                            "no_answer_false_positive", "update_correct"]) + " |")
    lines += ["", "## Interpretation and limitations", "",
              "- Outdated means factually replaced according to fixture labels. Stale means unreviewed evidence; these differ.",
              "- Valid-refactor scenarios have two checkpoints. Pending-review recall measures the cost of withholding a still-true memory; after-review measures recovery.",
              "- Missing-answer cases include changed facts whose replacements have not been recorded and four unrelated questions. Category rows separate them.",
              "- The semantic candidate stage returns nearest neighbors without an abstention threshold. Lifecycle filtering cannot by itself identify unrelated active memories.",
              "- Denominators are stored beside every aggregate in summary.csv; N/A values are excluded, never counted as zero.",
              "- Labels and review actions are authored fixtures, not automated truth verification or LLM extraction.",
              "- Five development scenarios and 25 reserved scenarios were fixed before execution. This is not an independently authored, blinded, or real-world benchmark.",
              "- Scenarios use small Python configuration files and six shared distractors. Category samples are small and templated; no significance or generalization claim is justified.",
              "- No model answers, agent coding success, tokenizer usage, or performance/latency comparison is measured.",
              "- Raw results preserve IDs, statuses, relevance labels, ranking reasons/scores, actual commits, diffs, and lifecycle events.", "",
              "## Observed failures / tradeoffs", ""]
    for variant in VARIANTS:
        subset = [r for r in report["results"] if r["variant"] == variant]
        bad = [r for r in subset if r["metrics"]["outdated_hit"] or r["metrics"]["no_answer_false_positive"]
               or r["metrics"]["recall_at_k"] == 0 or r["metrics"]["update_correct"] is False]
        lines.append(f"- {variant}: {len(bad)} checkpoints with at least one measured failure/tradeoff.")
        lines.extend(f'  - `{r["scenario"]}/{r["checkpoint"]}`: `{json.dumps(r["metrics"], sort_keys=True)}`'
                     for r in bad)
    lines += ["", "## Charts", ""]
    for partition in sorted({r["partition"] for r in report["summary"]}):
        lines += [f"![{partition} descriptive bars](charts/{partition}.svg)", ""]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    charts(report["summary"], output / "charts", report["limit"])


def run(output, partition="all", semantic=False, limit=5):
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    output = Path(output)
    # Never replace a previous experiment or mix incomplete and complete results.
    output.mkdir(parents=True, exist_ok=False)
    dataset = scenarios()
    serialized = json.dumps(dataset, indent=2) + "\n"
    (output / "scenarios.json").write_text(serialized, encoding="utf-8")
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    selected = [s for s in dataset["scenarios"] if partition == "all" or s["partition"] == partition]
    if not selected:
        raise ValueError("Unknown or empty partition")
    model = None
    if semantic:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
    rows, audits = [], []
    for fixture in selected:
        print(f'Evaluating {fixture["id"]} ({fixture["partition"]})', flush=True)
        found, audit = run_scenario(fixture, dataset["distractors"], model, semantic, limit)
        rows.extend(found)
        audits.append(audit)
    source_root = Path(__file__).resolve().parents[2]
    try:
        revision = git(source_root, "rev-parse", "HEAD")
        dirty = git(source_root, "status", "--porcelain")
    except (subprocess.SubprocessError, OSError):
        revision, dirty = None, "unavailable"
    versions = {}
    for package in ["chromadb", "sentence-transformers", "mcp"]:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    report = dict(mode="semantic_hybrid" if semantic else "keyword_file_proxy",
                  created_utc=datetime.now(timezone.utc).isoformat(), limit=limit,
                  dataset_sha256=digest, scenario_count=len(selected),
                  categories=dict(Counter(s["category"] for s in selected)),
                  environment=dict(python=platform.python_version(), platform=platform.platform(),
                                   versions=versions, engine_commit=revision, dirty_status=dirty,
                                   source_sha256={name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                                  for name in ["benchmark.py", "benchmark_data.py"]}),
                  summary=aggregate(rows), results=rows, audits=audits)
    write_report(report, output)
    print(f"Completed {len(selected)} scenarios / {len(rows)} variant-checkpoints: {output / 'REPORT.md'}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partition", choices=["all", "development", "held_out"], default="all")
    parser.add_argument("--semantic", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    run(args.output, args.partition, args.semantic, args.limit)


if __name__ == "__main__":
    main()
