"""Small controlled retrieval evaluation; no LLM or task-success claims.

Run: python -m oxmemory.evaluation --output evaluation-results.json
"""

import argparse
import json
import tempfile
from pathlib import Path
from time import perf_counter

from oxmemory.core.models import Memory, MemoryStatus
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore


SCENARIOS = [
    {"name": "authentication replacement", "query": "authentication", "file": "auth.py",
     "memories": [
         {"id": "old", "content": "Authentication uses JWT", "status": "superseded", "file_paths": ["auth.py"]},
         {"id": "new", "content": "Authentication uses cookies", "file_paths": ["auth.py"]},
         {"id": "noise", "content": "Logging uses JSON"}], "relevant": ["new"]},
    {"name": "unverified code change", "query": "cache", "file": "cache.py",
     "memories": [
         {"id": "stale", "content": "Cache expiry is 60 seconds", "status": "stale", "file_paths": ["cache.py"]},
         {"id": "noise", "content": "Logging uses JSON"}], "relevant": []},
    {"name": "same words different module", "query": "validation", "file": "payments.py",
     "memories": [
         {"id": "profile", "content": "Profile validation checks email", "file_paths": ["profile.py"]},
         {"id": "payment", "content": "Payment validation requires currency", "file_paths": ["payments.py"]}],
     "relevant": ["payment"]},
    {"name": "unchanged convention", "query": "timestamps", "file": "dates.py",
     "memories": [
         {"id": "dates", "content": "Store timestamps in UTC", "file_paths": ["dates.py"]},
         {"id": "noise", "content": "Use structured logging"}], "relevant": ["dates"]},
]


def metrics(ids: list[str], relevant: set[str], stale: set[str]) -> dict:
    hits = len(set(ids) & relevant)
    return {
        "precision": hits / len(ids) if ids else 0.0,
        "recall": hits / len(relevant) if relevant else None,
        "reciprocal_rank": next((1 / rank for rank, mid in enumerate(ids, 1) if mid in relevant), 0.0)
            if relevant else None,
        "stale_fraction": len(set(ids) & stale) / len(ids) if ids else 0.0,
        "correct_abstention": not ids if not relevant else None,
    }


def run_evaluation(semantic: bool = False, limit: int = 3) -> dict:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = []
    for scenario in SCENARIOS:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            markdown = MarkdownManager(root)
            markdown.initialize_brain("Synthetic evaluation")
            with MemoryStore(root, enable_vectors=semantic) as store:
                memories = [Memory(**item) for item in scenario["memories"]]
                for memory in memories:
                    markdown.add_memory(memory)
                setup_start = perf_counter()
                if semantic:
                    # Fail visibly if embeddings cannot run. Never label a fallback as semantic.
                    store.vector_store.add_many(memories)
                setup_ms = (perf_counter() - setup_start) * 1000
                for variant in ["no_memory", "basic_memory", "enhanced_memory"]:
                    start = perf_counter()
                    if variant == "no_memory":
                        results = []
                    elif variant == "basic_memory":
                        if semantic:
                            matches = store.vector_store.search(scenario["query"], min(limit, len(memories)))
                            results = [store.get(m["id"]) for m in matches]
                        else:
                            results = store._keyword_search(scenario["query"], limit)
                    else:
                        results = store.search(scenario["query"], limit, semantic=semantic,
                                               file_paths=[scenario["file"]])
                    elapsed = (perf_counter() - start) * 1000
                    ids = [m.id for m in results]
                    stale = {m.id for m in memories if m.status != MemoryStatus.ACTIVE}
                    rows.append({"scenario": scenario["name"], "variant": variant, "retrieved": ids,
                                 "metrics": metrics(ids, set(scenario["relevant"]), stale),
                                 "retrieval_ms": elapsed, "index_setup_ms": setup_ms,
                                 "content_bytes": sum(len(m.content.encode("utf-8")) for m in results),
                                 "markdown_bytes": sum(p.stat().st_size for p in root.rglob("*.md"))})
    summary = {}
    for variant in ["no_memory", "basic_memory", "enhanced_memory"]:
        group = [row for row in rows if row["variant"] == variant]
        summary[variant] = {}
        for key in group[0]["metrics"]:
            values = [row["metrics"][key] for row in group if row["metrics"][key] is not None]
            summary[variant][key] = sum(values) / len(values) if values else None
    return {"dataset": "4 hand-authored synthetic smoke scenarios; not a research benchmark",
            "mode": "semantic" if semantic else "keyword_only_proxy",
            "limit": limit,
            "limitations": ["No model responses or coding-task success are measured",
                            "No-memory metrics describe empty retrieval, not model capability",
                            "Keyword mode is not a reproduction of semantic 0xMemory",
                            "Single-run local latency is diagnostic, not a performance conclusion",
                            "Lifecycle labels are fixture inputs; use test_lifecycle.py for commit transitions",
                            "Bytes are not measured model tokens"],
            "summary": summary, "results": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--semantic", action="store_true")
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    report = json.dumps(run_evaluation(args.semantic, args.limit), indent=2)
    if args.output:
        args.output.write_text(report + "\n", encoding="utf-8")
    else:
        print(report)


if __name__ == "__main__":
    main()
