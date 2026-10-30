#!/usr/bin/env python3
"""Research-grade LoCoMo comparison for GEDAM and memory baselines.

Conditions:
  no_memory       empty context control
  full_history    all source dialogue turns (quality/compression reference)
  similarity      deterministic TF-IDF-like lexical similarity over observations
  baseline        0xMemory's existing baseline ranker
  gedam           0xMemory's evidence-aware ranker and context packer

This runner scores retrieval/evidence support, not free-form model answers. A
separate answer-generation harness must consume the same packets if answer
accuracy is required. Token counts are exact cl100k_base counts for rendered
payloads; they are not provider billing counters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STOP = set("a an the is are was were be been do does did how what which who when where why can could should would we our it its of for to in on at by with and or this that these those as from have has use used using tell me about".split())
TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")


def tokens(text: str) -> list[str]:
    text = str(text)
    return [x.lower() for x in TOKEN_RE.findall(text) if x.lower() not in STOP]


def tokenizer():
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base"), "cl100k_base"
    except Exception:
        return None, "utf8_bytes_div_3"


def token_count(text: str, enc) -> int:
    if enc is None:
        return (len(text.encode("utf-8")) + 2) // 3
    return len(enc.encode(text))


def normalize(text: str) -> list[str]:
    return tokens(text)


def f1(answer: str, context: str) -> float:
    gold, pred = Counter(normalize(answer)), Counter(normalize(context))
    overlap = sum((gold & pred).values())
    if not gold or not pred or not overlap:
        return 0.0
    precision, recall = overlap / sum(pred.values()), overlap / sum(gold.values())
    return 2 * precision * recall / (precision + recall)


def session_rows(record: dict) -> list[dict]:
    rows = []
    for key, value in record["conversation"].items():
        if not key.startswith("session_") or key.endswith("date_time") or not isinstance(value, list):
            continue
        for turn in value:
            rows.append(turn)
    return rows


def observations(record: dict) -> list[dict]:
    rows = []
    for key, people in record.get("observation", {}).items():
        session = key.split("_")[1]
        for speaker, facts in people.items():
            for index, pair in enumerate(facts):
                if not isinstance(pair, list) or len(pair) < 2:
                    continue
                evidence_ids = pair[1] if isinstance(pair[1], list) else [pair[1]]
                rows.append({"id": f"obs-{session}-{speaker}-{index}", "evidence_ids": evidence_ids, "content": pair[0], "session": session, "speaker": speaker, "ordinal": index})
    return rows


def tfidf_rank(query: str, records: list[dict], limit: int) -> list[dict]:
    q = set(tokens(query))
    docs = [set(tokens(r["content"])) for r in records]
    df = Counter(t for d in docs for t in d)
    n = max(len(docs), 1)
    scored = []
    for r, doc in zip(records, docs):
        overlap = q & doc
        score = sum((1 + math.log(n / (1 + df[t]))) for t in overlap)
        score = score / math.sqrt(max(len(doc), 1)) if score else 0.0
        scored.append((score, r))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [dict(r, score=score, reasons=["tfidf_token_overlap"]) for score, r in scored[:limit] if score > 0]


def render_records(records: list[dict]) -> str:
    return "\n\n".join(f"[{r['id']}] {r['content']}" for r in records)


def render_history(turns: list[dict]) -> str:
    return "\n".join(f"[{t.get('dia_id', '')}] {t.get('speaker', '')}: {t.get('text', '')}" for t in turns)


def run(input_path: Path, output: Path, limit: int) -> dict:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    enc, tokenizer_name = tokenizer()
    rows = []
    conditions = ["no_memory", "full_history", "similarity", "baseline", "gedam"]
    from oxmemory.core.config import get_default_config, save_config
    from oxmemory.core.models import Memory, RetrievalConfig
    from oxmemory.storage.markdown import MarkdownManager
    from oxmemory.storage.memory_store import MemoryStore

    for conversation in data:
        sample_id = conversation["sample_id"]
        obs = observations(conversation)
        turns = session_rows(conversation)
        obs_by_evidence = {e: r for r in obs for e in r["evidence_ids"]}
        with tempfile.TemporaryDirectory(prefix="locomo-memory-") as temp:
            root = Path(temp)
            MarkdownManager(root).initialize_brain(f"LoCoMo {sample_id}")
            config = get_default_config(f"locomo-{sample_id}")
            save_config(config, root)
            with MemoryStore(root, enable_vectors=False) as store:
                store._config = config
                for record in obs:
                    store.markdown.add_memory(Memory(id=record["id"], content=record["content"], tags=[record["speaker"], f"session_{record['session']}"], source="locomo_observation"))
                for qa_index, qa in enumerate(conversation["qa"]):
                    gold_ids = set(qa.get("evidence", []))
                    gold_records = [obs_by_evidence[g] for g in gold_ids if g in obs_by_evidence]
                    evidence_by_memory_id = {}
                    for record in obs:
                        evidence_by_memory_id[record["id"]] = record["evidence_ids"]
                    for condition in conditions:
                        if condition == "no_memory":
                            retrieved, context = [], ""
                            status = "no_memory"
                        elif condition == "full_history":
                            retrieved, context = [], render_history(turns)
                            status = "full_history"
                        elif condition == "similarity":
                            retrieved = tfidf_rank(qa["question"], obs, limit)
                            context = render_records(retrieved)
                            status = "similarity"
                        else:
                            architecture = "edam" if condition == "gedam" else "baseline"
                            store._config.retrieval = RetrievalConfig(architecture=architecture, relevance_gate=condition == "gedam")
                            packed = store.recall_context(qa["question"], token_budget=4000, semantic=False, limit=limit)
                            retrieved = [dict(item["memory"], score=item.get("score"), reasons=item.get("reasons", [])) for item in packed.get("results", [])]
                            context = packed.get("context", "")
                            status = packed.get("status")
                        if condition == "full_history":
                            ranked_ids = [e for record in obs for e in record["evidence_ids"]]
                        else:
                            ranked_ids = [e for r in retrieved for e in evidence_by_memory_id.get(r["id"], [])]
                        first_rank = next((i + 1 for i, rid in enumerate(ranked_ids) if rid in gold_ids), None)
                        relevant_returned = len(set(ranked_ids) & gold_ids)
                        rows.append({
                            "sample_id": sample_id, "qa_index": qa_index, "category": qa.get("category"), "question": qa["question"], "answer": qa.get("answer", ""), "gold_evidence": sorted(gold_ids), "condition": condition, "ranked_evidence": ranked_ids, "retrieval_status": status,
                            "recall_at_k": relevant_returned / len(gold_ids) if gold_ids else None,
                            "mrr": 1 / first_rank if first_rank else 0.0 if gold_ids else None,
                            "precision_at_k": relevant_returned / len(ranked_ids) if ranked_ids else 0.0,
                            "evidence_recall_any": bool(set(ranked_ids) & gold_ids) if gold_ids else None,
                            "irrelevant_rate": 1 - relevant_returned / len(ranked_ids) if ranked_ids else 0.0,
                            "answer_evidence_f1": f1(qa.get("answer", ""), context),
                            "context_tokens": token_count(context, enc), "context_bytes": len(context.encode("utf-8")),
                            "source_tokens": token_count(render_history(turns), enc),
                            "compression_vs_full_history": 1 - token_count(context, enc) / max(token_count(render_history(turns), enc), 1),
                            "retrieved_count": len(ranked_ids), "gold_count": len(gold_ids),
                        })
    return {
        "benchmark": "LoCoMo GEDAM memory comparison v2",
        "created_utc": datetime.now(UTC).isoformat(), "dataset": input_path.name,
        "dataset_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(), "dataset_url": "https://github.com/snap-research/LoCoMo/blob/main/data/locomo10.json",
        "paper": "https://aclanthology.org/2024.acl-long.747/", "tokenizer": tokenizer_name,
        "conditions": conditions, "conversation_count": len(data), "qa_count": len(rows) // len(conditions), "row_count": len(rows), "limit": limit,
        "environment": {"python": sys.version, "platform": platform.platform(), "engine_commit": __import__('subprocess').run(['git','-C',str(ROOT),'rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()},
        "results": rows,
        "limitations": ["LoCoMo provides evidence IDs but does not provide stale/deletion labels; stale-hit and valid-memory-suppression require a separate temporal/negative benchmark.", "Answer evidence F1 measures support in the retrieved packet, not free-form LLM answer correctness.", "Similarity is a deterministic lexical TF-IDF-like retriever, not an external vendor product.", "Provider token/cost usage requires an answer-generation run; context counts here are exact rendered-payload counts."]
    }


def summarize(report: dict) -> list[dict]:
    out = []
    for condition in report["conditions"]:
        selected = [r for r in report["results"] if r["condition"] == condition]
        def avg(k):
            vals = [r[k] for r in selected if r[k] is not None]
            return sum(vals) / len(vals) if vals else None
        out.append({"condition": condition, "n": len(selected), "recall_at_k": avg("recall_at_k"), "mrr": avg("mrr"), "precision_at_k": avg("precision_at_k"), "evidence_recall_any": avg("evidence_recall_any"), "irrelevant_rate": avg("irrelevant_rate"), "answer_evidence_f1": avg("answer_evidence_f1"), "mean_context_tokens": avg("context_tokens"), "median_context_tokens": statistics.median([r["context_tokens"] for r in selected]), "mean_source_tokens": avg("source_tokens"), "mean_compression_vs_full_history": avg("compression_vs_full_history")})
    return out


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--input", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--limit", type=int, default=5); args = parser.parse_args()
    report = run(args.input, args.output, args.limit); summary = summarize(report); report["summary"] = summary
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    import csv
    with (args.output / "summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
    lines = ["# LoCoMo research benchmark: GEDAM versus memory baselines", "", f"Dataset: `{report['dataset']}` (SHA-256 `{report['dataset_sha256']}`).", f"Conversations: {report['conversation_count']}; QA items: {report['qa_count']}; top-k: {report['limit']}; tokenizer: `{report['tokenizer']}`.", "", "| Condition | n | Recall@k | MRR | Precision@k | Evidence recall-any | Irrelevant rate | Answer evidence F1 | Mean context tokens | Median context tokens | Mean source tokens | Compression vs full history |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for s in summary:
        lines.append("| {condition} | {n} | {recall_at_k:.3f} | {mrr:.3f} | {precision_at_k:.3f} | {evidence_recall_any:.3f} | {irrelevant_rate:.3f} | {answer_evidence_f1:.3f} | {mean_context_tokens:.1f} | {median_context_tokens:.1f} | {mean_source_tokens:.1f} | {mean_compression_vs_full_history:.3%} |".format(**{k:(0 if v is None else v) for k,v in s.items()}))
    lines += ["", "## Conditions", "", "- `no_memory`: empty context control.", "- `full_history`: all dialogue turns; quality and compression reference.", "- `similarity`: deterministic lexical TF-IDF-like observation retriever.", "- `baseline`: 0xMemory existing baseline ranker with lifecycle/relevance safeguards disabled.", "- `gedam`: 0xMemory GEDAM ranker with relevance gate and adaptive packing.", "", "## Reproducibility", "", "Raw per-question rows are in `results.json`; aggregate CSV is `summary.csv`. The source dataset is the authors' LoCoMo release and is cited in the report metadata.", "", "## Limits", "", *[f"- {x}" for x in report["limitations"]], ""]
    (args.output / "REPORT.md").write_text("\n".join(lines))


if __name__ == "__main__": main()
