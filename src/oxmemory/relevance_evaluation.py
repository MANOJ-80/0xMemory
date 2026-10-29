"""Development-only threshold selection, then one frozen-policy test on new cases."""

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

from oxmemory.core.models import Memory, RetrievalConfig
from oxmemory.relevance_cases import dataset
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.retrieval import build_context, rank_memories
from oxmemory.storage.vector_store import VectorStore


def metrics(rows):
    answerable = [r for r in rows if r["relevant"]]
    missing = [r for r in rows if not r["relevant"]]
    def first_relevant(row, ids_key="retrieved"):
        return next((1 / rank for rank, memory_id in enumerate(row[ids_key], 1)
                     if memory_id in row["relevant"]), 0.0)

    def dcg(row, ids_key="retrieved"):
        return sum(1 / math.log2(rank + 1)
                   for rank, memory_id in enumerate(row[ids_key], 1)
                   if memory_id in row["relevant"])

    def ndcg(row, ids_key="retrieved"):
        ideal = sum(1 / math.log2(rank + 1)
                    for rank in range(1, min(len(row["relevant"]), 5) + 1))
        return dcg(row, ids_key) / ideal if ideal else 0.0

    latencies = sorted(r["latency_ms"] for r in rows)
    p95 = latencies[min(len(latencies) - 1, int(0.95 * len(latencies)))] if latencies else 0.0
    abstentions = [r for r in rows if not r["retrieved"]]
    correct_abstentions = [r for r in missing if not r["retrieved"]]
    assessed = [decision for row in rows for decision in row["ranking"]
                if decision.get("evidence_validation")]
    supported = [decision for decision in assessed
                 if decision["evidence_validation"].get("state") == "supported"]
    labeled_support = [
        (decision, row["evidence_support_labels"][decision["id"]])
        for row in rows for decision in row["ranking"]
        if decision["id"] in row.get("evidence_support_labels", {})
    ]
    outdated_denominator = sum(len(row.get("outdated_memory_ids", [])) for row in rows)
    valid_denominator = sum(len(row.get("valid_memory_ids", [])) for row in rows)
    conflict_labeled = [row for row in rows if "expected_conflict" in row]
    return dict(
        answerable_n=len(answerable),
        no_answer_n=len(missing),
        recall=sum(bool(set(r["retrieved"]) & set(r["relevant"])) for r in answerable)
        / len(answerable),
        false_abstention=sum(not r["retrieved"] for r in answerable) / len(answerable),
        no_answer_fp=sum(bool(r["retrieved"]) for r in missing) / len(missing),
        no_answer_recall=1.0 - sum(bool(r["retrieved"]) for r in missing) / len(missing),
        no_answer_precision=(len(correct_abstentions) / len(abstentions) if abstentions else 0.0),
        precision_at_5=sum(len(set(r["retrieved"][:5]) & set(r["relevant"])) / 5
                           for r in answerable) / len(answerable),
        mrr=sum(first_relevant(r) for r in answerable) / len(answerable),
        ndcg_at_5=sum(ndcg(r) for r in answerable) / len(answerable),
        budgeted_recall=sum(bool(set(r["budget_retrieved"]) & set(r["relevant"]))
                            for r in answerable) / len(answerable),
        mean_context_bytes=(sum(r["context_bytes"] for r in rows) / len(rows)) if rows else 0,
        mean_context_tokens=(sum(r["context_tokens"] for r in rows) / len(rows)) if rows else 0,
        latency_p50_ms=(latencies[len(latencies) // 2] if latencies else 0.0),
        latency_p95_ms=p95,
        evidence_anchor_continuity_rate=(len(supported) / len(assessed) if assessed else None),
        evidence_support_rate=(sum(bool(label) for _, label in labeled_support) /
                               len(labeled_support) if labeled_support else None),
        outdated_memory_retrieval_rate=(
            sum(len(set(row["retrieved"]) & set(row.get("outdated_memory_ids", [])))
                for row in rows) / outdated_denominator if outdated_denominator else None
        ),
        valid_memory_suppression_rate=(
            sum(len(set(row.get("valid_memory_ids", [])) - set(row["retrieved"]))
                for row in rows) / valid_denominator if valid_denominator else None
        ),
        contradiction_detection_recall=(
            sum(row["retrieval_status"] == "abstained_conflict" for row in conflict_labeled
                if row["expected_conflict"]) /
            sum(bool(row["expected_conflict"]) for row in conflict_labeled)
            if any(row["expected_conflict"] for row in conflict_labeled) else None
        ),
        contradiction_false_abstention_rate=(
            sum(row["retrieval_status"] == "abstained_conflict" for row in conflict_labeled
                if not row["expected_conflict"]) /
            sum(not row["expected_conflict"] for row in conflict_labeled)
            if any(not row["expected_conflict"] for row in conflict_labeled) else None
        ),
        retrieval_model_calls=0,
        retrieval_model_tokens=0,
        coding_task_success_rate=None,
        coding_test_pass_rate=None,
    )


def prepare(cases, model):
    prepared = []
    for case in cases:
        with tempfile.TemporaryDirectory(prefix="relevance-eval-") as tmp:
            root = Path(tmp)
            markdown = MarkdownManager(root)
            markdown.initialize_brain("Relevance test")
            memories = [
                Memory(id=f"m{i}", **(
                    {"content": text} if isinstance(text, str) else text
                ))
                for i, text in enumerate(case["memories"])
            ]
            for memory in memories:
                markdown.add_memory(memory)
            vector = VectorStore(root)
            vector._embedder = model
            try:
                vector.add_many(memories)
                candidates = vector.search(case["query"], limit=len(memories))
                assert len(candidates) == len(memories), "Incomplete semantic corpus"
                assert all("similarity" in r for r in candidates)
                prepared.append((case, memories, candidates))
            finally:
                vector.close()
    return prepared


def evaluate(prepared, threshold, gated, architecture="baseline",
             selection_strategy="adaptive", policy_overrides=None,
             include_history=False, edam_similarity=None):
    rows = []
    for case, memories, candidates in prepared:
        started = time.perf_counter()
        proxy = SimpleNamespace(
            markdown=SimpleNamespace(get_all_memories=lambda: memories),
            vector_store=SimpleNamespace(search=lambda *a, **kw: candidates),
        )
        if architecture == "none":
            ranked = []
        else:
            similarity_threshold = (edam_similarity if architecture == "edam"
                                    and edam_similarity is not None else threshold)
            retrieval_policy = RetrievalConfig(
                architecture=architecture, relevance_gate=gated,
                min_similarity=similarity_threshold,
                **(policy_overrides or {}),
            )
            ranked = rank_memories(
                proxy,
                case["query"],
                5,
                None,
                True,
                [],
                [],
                relevance_gate=gated,
                min_similarity=similarity_threshold,
                policy=retrieval_policy,
                include_history=include_history,
            )
        packed = build_context(ranked, 1500, query=case["query"],
                               selection_strategy=selection_strategy)
        latency_ms = (time.perf_counter() - started) * 1000
        rows.append(
            dict(
                id=case["id"],
                query=case["query"],
                relevant=case["relevant"],
                outdated_memory_ids=case.get("outdated_memory_ids", []),
                valid_memory_ids=case.get("valid_memory_ids", []),
                evidence_support_labels=case.get("evidence_support_labels", {}),
                **({"expected_conflict": case["expected_conflict"]}
                   if "expected_conflict" in case else {}),
                retrieved=[r["memory"].id for r in ranked],
                budget_retrieved=[r["memory"]["id"] for r in packed["results"]],
                context_bytes=packed["budget_used_bytes"],
                context_tokens=packed["budget_used"],
                latency_ms=latency_ms,
                candidates=[
                    dict(
                        id=r["id"],
                        content=r["content"],
                        cosine=r["similarity"],
                        distance=r["distance"],
                    )
                    for r in candidates
                ],
                ranking=[
                    dict(id=r["memory"].id, score=r["score"], reasons=r["reasons"],
                         score_components=r.get("score_components", {}),
                         evidence_validation=r.get("evidence_validation")) for r in ranked
                ],
                diagnostics=getattr(ranked, "diagnostics", []),
                retrieval_status=getattr(ranked, "status", "abstained_no_candidates"),
                query_plan=getattr(ranked, "query_plan", {}),
                budget_diagnostics=packed["diagnostics"],
            )
        )
    return rows


def run(output, phase, policy_path=None):
    from sentence_transformers import SentenceTransformer

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    frozen = json.dumps(dataset(), indent=2).encode()
    digest = hashlib.sha256(frozen).hexdigest()
    (output / "scenarios.json").write_bytes(frozen)
    project_root = Path(__file__).resolve().parents[2]
    try:
        commit = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    source_files = [
        Path(__file__),
        Path(__file__).with_name("storage") / "retrieval.py",
        Path(__file__).with_name("storage") / "query_planner.py",
        Path(__file__).with_name("storage") / "code_index.py",
        Path(__file__).with_name("storage") / "memory_store.py",
        Path(__file__).with_name("storage") / "repository.py",
        Path(__file__).with_name("core") / "models.py",
    ]
    source_hashes = {str(path.relative_to(project_root)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in source_files if path.is_file()}
    partition = "development" if phase == "calibrate" else "held_out"
    cases = [c for c in dataset() if c["partition"] == partition]
    policy = None
    if phase == "test":
        policy = json.loads(Path(policy_path).read_text())
        if policy["dataset_sha256"] != digest:
            raise ValueError("Policy and test dataset hashes differ")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    prepared = prepare(cases, model)
    if phase == "calibrate":
        trials = []
        for threshold in [i / 100 for i in range(25, 76, 5)]:
            result = metrics(evaluate(prepared, threshold, True))
            # Missed useful memories cost twice as much as no-answer false positives.
            loss = 2 * (1 - result["recall"]) + result["no_answer_fp"]
            trials.append(dict(threshold=threshold, loss=loss, **result))
        best = min(trials, key=lambda r: (r["loss"], r["threshold"]))
        edam_trials = []
        for similarity_threshold in [i / 100 for i in range(25, 76, 5)]:
            for score_threshold in [i / 100 for i in range(10, 61, 5)]:
                result = metrics(evaluate(
                    prepared, similarity_threshold, True, architecture="edam",
                    selection_strategy="adaptive",
                    policy_overrides={"min_edam_score": score_threshold},
                    edam_similarity=similarity_threshold,
                ))
                loss = 2 * (1 - result["recall"]) + result["no_answer_fp"]
                edam_trials.append(dict(
                    similarity_threshold=similarity_threshold,
                    min_edam_score=score_threshold, loss=loss, **result,
                ))
        best_edam = min(edam_trials, key=lambda r: (
            r["loss"], r["similarity_threshold"], r["min_edam_score"]
        ))
        policy = dict(
            threshold=best["threshold"],
            edam_similarity_threshold=best_edam["similarity_threshold"],
            edam_min_score=best_edam["min_edam_score"],
            dataset_sha256=digest,
            criterion="minimize 2*(1-recall)+no_answer_fp; ties choose lower threshold",
            model="all-MiniLM-L6-v2",
            development_trials=trials,
            edam_development_trials=edam_trials,
        )
        (output / "policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    variants = [
        ("no_memory", False, "none", "ranked", {}, False),
        # Four comparison conditions share the exact same memory corpus.
        ("basic_retrieval", False, "baseline", "ranked", {}, True),
        ("current_0xmemory", False, "baseline", "ranked", {}, False),
        ("edam", True, "edam", "adaptive",
         {"min_edam_score": policy.get("edam_min_score", RetrievalConfig().min_edam_score)}, False),
        # Component ablations preserve the same test data and frozen threshold.
        ("ungated", False, "baseline", "ranked", {}, False),
        ("gated", True, "baseline", "ranked", {}, False),
        ("edam_no_evidence", True, "edam", "adaptive",
         {"w_evidence": 0.0,
          "min_edam_score": policy.get("edam_min_score", RetrievalConfig().min_edam_score)}, False),
        ("edam_no_abstention", False, "edam", "adaptive", {"min_edam_score": 0.0}, False),
        ("edam_no_budget", True, "edam", "ranked",
         {"min_edam_score": policy.get("edam_min_score", RetrievalConfig().min_edam_score)}, False),
    ]
    rows = {
        name: evaluate(prepared, policy["threshold"], gated, architecture,
                       selection_strategy, overrides, include_history,
                       policy.get("edam_similarity_threshold"))
        for name, gated, architecture, selection_strategy, overrides, include_history in variants
    }
    report = dict(
        partition=partition,
        policy=policy,
        dataset_sha256=digest,
        environment={"git_commit": commit, "python": sys.version,
                     "platform": platform.platform(),
                     "embedding_model": "all-MiniLM-L6-v2",
                     "source_sha256": source_hashes},
        summary={name: metrics(r) for name, r in rows.items()},
        results=rows,
        retrieval_policies={
            "no_memory": {"retrieval": False},
            "basic_retrieval": {"architecture": "baseline", "include_history": True,
                                "relevance_gate": False},
            "current_0xmemory": {"architecture": "baseline", "include_history": False,
                                 "relevance_gate": False},
            "ungated": {"architecture": "baseline", "relevance_gate": False},
            "gated": {"architecture": "baseline", "relevance_gate": True,
                      "min_similarity": policy["threshold"]},
            "edam": {"architecture": "edam", "relevance_gate": True,
                     "min_similarity": policy.get("edam_similarity_threshold", policy["threshold"]),
                     "min_edam_score": policy.get("edam_min_score", RetrievalConfig().min_edam_score)},
            "edam_no_evidence": {"architecture": "edam", "w_evidence": 0.0,
                                 "min_edam_score": policy.get("edam_min_score")},
            "edam_no_abstention": {"architecture": "edam", "relevance_gate": False,
                                    "min_edam_score": 0.0},
            "edam_no_budget": {"architecture": "edam", "selection_strategy": "ranked"},
        },
        limitations=[
            "Assistant-authored synthetic data; independent label review pending",
            "No-answer labels include missing rationale and ownership questions",
            "Cosine similarity measures relatedness, not answer entailment",
            "No production coding-success or general accuracy claim",
        ],
    )
    (output / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        f"# Relevance experiment: {partition}",
        "",
        f"Frozen threshold: **{policy['threshold']}**. Model: all-MiniLM-L6-v2.",
        "",
        "| Variant | P@5 | Recall@5 | MRR | nDCG@5 | Budget recall | Mean tokens | Mean bytes | p95 ms | No-answer FP |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, summary in report["summary"].items():
        lines.append(
            f"| {name} | {summary['precision_at_5']:.1%} | {summary['recall']:.1%} | "
            f"{summary['mrr']:.3f} | {summary['ndcg_at_5']:.3f} | "
            f"{summary['budgeted_recall']:.1%} | {summary['mean_context_tokens']:.0f} | "
            f"{summary['mean_context_bytes']:.0f} | "
            f"{summary['latency_p95_ms']:.2f} | {summary['no_answer_fp']:.1%} |"
        )
    lines += [
        "",
        f"Answerable cases: {sum(bool(c['relevant']) for c in cases)}; "
        f"no-answer cases: {sum(not c['relevant'] for c in cases)}.",
        "",
        "## Failures",
        "",
    ]
    for row in rows["gated"]:
        if (not row["relevant"] and row["retrieved"]) or (
            row["relevant"] and not set(row["relevant"]) & set(row["retrieved"])
        ):
            lines.append(
                f"- {row['id']}: {row['query']} Returned {row['retrieved']}; "
                f"expected relevant IDs {row['relevant']}."
            )
    lines += ["", "## Limits", "", *[f"- {s}" for s in report["limitations"]]]
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            dict(partition=partition, threshold=policy["threshold"], summary=report["summary"]),
            indent=2,
        )
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["calibrate", "test"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy", type=Path)
    args = parser.parse_args()
    if args.phase == "test" and args.policy is None:
        parser.error("--policy is required for the test phase")
    run(args.output, args.phase, args.policy)


if __name__ == "__main__":
    main()
