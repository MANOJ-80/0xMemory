"""Hybrid reciprocal-rank fusion with explicit file/symbol relevance."""

import logging
import re

from oxmemory.core.models import Memory, MemoryStatus

logger = logging.getLogger(__name__)


def rank_memories(
    store, query, limit, memory_types, semantic, file_paths, symbols, include_history,
):
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if not query.strip():
        return []
    files = set(Memory(content="paths", file_paths=file_paths or []).file_paths)
    symbols = set(symbols or [])
    memories = {m.id: m for m in store.markdown.get_all_memories()
                if (include_history or m.status == MemoryStatus.ACTIVE)
                and (not memory_types or m.type in memory_types)}
    scores, reasons = {}, {}

    def contribute(ids, label, weight=1.0):
        for rank, memory_id in enumerate(ids, 1):
            if memory_id in memories:
                scores[memory_id] = scores.get(memory_id, 0) + weight / (60 + rank)
                reasons.setdefault(memory_id, []).append(label)

    words = set(re.findall(r"\w+", query.lower()))
    keyword = []
    for memory in memories.values():
        text = " ".join([memory.content, *memory.tags, *memory.symbols]).lower()
        overlap = len(words & set(re.findall(r"\w+", text)))
        if overlap:
            keyword.append((memory.id, overlap / max(len(words), 1)))
    keyword.sort(key=lambda item: (-item[1], item[0]))
    contribute([item[0] for item in keyword], "keyword match")
    if semantic and memories:
        try:
            if store.vector_store:
                results = store.vector_store.search(
                    query, limit=max(1, len(store.markdown.get_all_memories())),
                    memory_types=memory_types,
                )
                contribute([r["id"] for r in results if r["id"] in memories], "semantic match")
        except Exception as exc:
            logger.warning("Semantic search unavailable; using keyword/file matches: %s", exc)
    for memory in memories.values():
        if files & set(memory.file_paths):
            contribute([memory.id], "linked file match", 1.5)
        if symbols & set(memory.symbols):
            contribute([memory.id], "linked symbol match", 1.5)
    ordered = sorted(scores, key=lambda mid: (-scores[mid], mid))[:limit]
    return [
        {"memory": memories[mid], "score": scores[mid], "reasons": reasons[mid]}
        for mid in ordered
    ]


def build_context(ranked: list[dict], token_budget: int) -> dict:
    if not 1 <= token_budget <= 100000:
        raise ValueError("token_budget must be between 1 and 100000")
    blocks, selected, used = [], [], 0
    for item in ranked:
        memory = item["memory"]
        evidence = ", ".join(memory.file_paths) or "conversation/manual"
        block = (f"[{memory.id}; {memory.status.value}] {memory.content}\n"
                 f"Evidence: {evidence}; commit: {memory.commit_sha or 'unrecorded'}\n"
                 f"Retrieved because: {', '.join(item['reasons'])}")
        # UTF-8 byte count is a conservative proxy, not a model-specific token count.
        cost = len((block + ("\n\n" if blocks else "")).encode("utf-8"))
        if used + cost > token_budget:
            continue  # Never truncate a decision or its evidence halfway through.
        blocks.append(block)
        used += cost
        selected.append({"memory": memory.model_dump(mode="json", exclude={"revisions"}),
                         "score": item["score"], "reasons": item["reasons"]})
    return {"context": "\n\n".join(blocks), "results": selected,
            "budget_used": used, "budget_unit": "conservative_utf8_bytes",
            "token_budget": token_budget, "omitted": len(ranked) - len(selected)}
