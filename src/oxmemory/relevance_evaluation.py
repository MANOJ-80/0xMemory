"""Development-only threshold selection, then one frozen-policy test on new cases."""

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from oxmemory.core.models import Memory
from oxmemory.relevance_cases import dataset
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.retrieval import rank_memories
from oxmemory.storage.vector_store import VectorStore


def metrics(rows):
    answerable = [r for r in rows if r["relevant"]]
    missing = [r for r in rows if not r["relevant"]]
    return dict(
        answerable_n=len(answerable),
        no_answer_n=len(missing),
        recall=sum(bool(set(r["retrieved"]) & set(r["relevant"])) for r in answerable)
        / len(answerable),
        false_abstention=sum(not r["retrieved"] for r in answerable) / len(answerable),
        no_answer_fp=sum(bool(r["retrieved"]) for r in missing) / len(missing),
    )


def prepare(cases, model):
    prepared = []
    for case in cases:
        with tempfile.TemporaryDirectory(prefix="relevance-eval-") as tmp:
            root = Path(tmp)
            markdown = MarkdownManager(root)
            markdown.initialize_brain("Relevance test")
            memories = [Memory(id=f"m{i}", content=text) for i, text in enumerate(case["memories"])]
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


def evaluate(prepared, threshold, gated):
    rows = []
    for case, memories, candidates in prepared:
        proxy = SimpleNamespace(
            markdown=SimpleNamespace(get_all_memories=lambda: memories),
            vector_store=SimpleNamespace(search=lambda *a, **kw: candidates),
        )
        ranked = rank_memories(
            proxy,
            case["query"],
            5,
            None,
            True,
            [],
            [],
            False,
            relevance_gate=gated,
            min_similarity=threshold,
        )
        rows.append(
            dict(
                id=case["id"],
                query=case["query"],
                relevant=case["relevant"],
                retrieved=[r["memory"].id for r in ranked],
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
                    dict(id=r["memory"].id, score=r["score"], reasons=r["reasons"]) for r in ranked
                ],
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
        policy = dict(
            threshold=best["threshold"],
            dataset_sha256=digest,
            criterion="minimize 2*(1-recall)+no_answer_fp; ties choose lower threshold",
            model="all-MiniLM-L6-v2",
            development_trials=trials,
        )
        (output / "policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    rows = {
        name: evaluate(prepared, policy["threshold"], gated)
        for name, gated in [("ungated", False), ("gated", True)]
    }
    report = dict(
        partition=partition,
        policy=policy,
        dataset_sha256=digest,
        summary={name: metrics(r) for name, r in rows.items()},
        results=rows,
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
        "| Variant | Answer recall | False abstention | No-answer false positive |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, summary in report["summary"].items():
        lines.append(
            f"| {name} | {summary['recall']:.1%} | "
            f"{summary['false_abstention']:.1%} | {summary['no_answer_fp']:.1%} |"
        )
    lines += [
        "",
        f"Answerable cases: {len(cases) // 2}; no-answer cases: {len(cases) // 2}.",
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
