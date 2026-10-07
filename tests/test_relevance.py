"""Behavioral checks for abstention, ranking eligibility, and real-score math."""

from types import SimpleNamespace

import pytest

from oxmemory.core.models import Memory
from oxmemory.relevance_cases import dataset
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore
from oxmemory.storage.relevance import cosine_similarity, relevant
from oxmemory.storage.retrieval import rank_memories


def test_cosine_is_independent_of_embedding_scale():
    assert cosine_similarity([2, 0], [4, 0]) == 1
    assert cosine_similarity([1, 0], [0, 5]) == 0
    assert cosine_similarity([1, 0], [-9, 0]) == -1
    assert cosine_similarity([0, 0], [1, 1]) == 0
    with pytest.raises(ValueError):
        cosine_similarity([1], [1, 2])


def test_file_hint_cannot_bypass_low_similarity():
    noise = Memory(id="noise", content="Background colour is green", file_paths=["config.py"])
    answer = Memory(id="answer", content="Database pooling allows twenty clients")
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: [noise, answer]),
        vector_store=SimpleNamespace(
            search=lambda *a, **k: [
                dict(id=noise.id, similarity=0.1),
                dict(id=answer.id, similarity=0.8),
            ]
        ),
    )
    found = rank_memories(
        proxy,
        "connection capacity",
        5,
        None,
        True,
        ["config.py"],
        [],
        False,
        relevance_gate=True,
        min_similarity=0.4,
    )
    assert [item["memory"].id for item in found] == ["answer"]


def test_keyword_fallback_rejects_stopword_only_overlap():
    memory = Memory(content="The server is configured with JSON logging")
    assert not relevant("Who is the compliance officer?", memory)
    assert not relevant("What is the?", memory)
    assert relevant("JSON logging", memory)
    assert not relevant("JSON logging", memory, float("nan"))
    with pytest.raises(ValueError):
        relevant("logging", memory, 0.5, 2)


def test_context_explains_absence_vs_budget(tmp_path):
    MarkdownManager(tmp_path).initialize_brain("Abstention")
    with MemoryStore(tmp_path, enable_vectors=False) as store:
        store.add("Database uses SQLite")
        missing = store.recall_context("Who owns incident escalation?", relevance_gate=True)
        assert missing["abstained"] is True
        assert missing["abstention_reason"] == "no_relevant_memory"
        small = store.recall_context("Database", token_budget=1)
        assert small["abstention_reason"] == "context_budget"
        assert not store.recall_context("Database")["abstained"]


def test_gate_is_opt_in_and_config_reaches_retrieval(tmp_path):
    from oxmemory.core.config import get_default_config, load_config, save_config
    from oxmemory.core.models import RetrievalConfig

    MarkdownManager(tmp_path).initialize_brain("Configuration")
    save_config(get_default_config("Configuration"), tmp_path)
    config = load_config(tmp_path)
    assert not config.retrieval.relevance_gate
    config.retrieval = RetrievalConfig(relevance_gate=True, min_similarity=0.7)
    save_config(config, tmp_path)
    with MemoryStore(tmp_path, enable_vectors=False) as store:
        memory = store.add("The interface is green")
        store._vector_store = SimpleNamespace(
            search=lambda *a, **kw: [dict(id=memory.id, similarity=0.6)], close=lambda: None
        )
        assert store.search("interface") == []
        assert store.search_ranked("interface", relevance_gate=False)


def test_new_partitions_are_disjoint_and_balanced():
    cases = dataset()
    dev = [c for c in cases if c["partition"] == "development"]
    test = [c for c in cases if c["partition"] == "held_out"]
    assert len(dev) == 8 and len(test) == 16
    assert sum(bool(c["relevant"]) for c in dev) == 4
    assert sum(bool(c["relevant"]) for c in test) == 8
    assert not {c["id"] for c in dev} & {c["id"] for c in test}
