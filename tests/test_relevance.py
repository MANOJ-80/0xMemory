"""Behavioral checks for abstention, ranking eligibility, and real-score math."""

from types import SimpleNamespace

import pytest

from oxmemory.core.models import Memory, RetrievalConfig
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


def test_query_planner_extracts_natural_dates_and_rationale_is_read_from_claim():
    from oxmemory.storage.query_planner import analyze_query

    plan = analyze_query("Which database did we use on Sep 12, 2026?")
    assert plan.as_of == "2026-09-12"
    assert plan.historical is True

    memory = Memory(id="decision", content="We chose PostgreSQL because it supports our workload.")
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: [memory]), vector_store=None,
        project_dir=".",
    )
    result = rank_memories(proxy, "Why did we choose PostgreSQL?", 5, None, False, [], [], False,
                           policy=RetrievalConfig())
    assert [row["memory"].id for row in result] == ["decision"]


def test_edam_scores_expose_normalized_components_and_preserve_baseline():
    memory = Memory(id="supported", content="Database SQLite storage", utility=0.8,
                    utility_observations=3)
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: [memory]),
        vector_store=None,
    )
    edam = rank_memories(proxy, "Database SQLite", 5, None, False, [], [], False,
                         policy=RetrievalConfig())
    assert edam[0]["score_components"].keys() >= {
        "relevance", "evidence", "freshness", "scope", "utility"
    }
    baseline = rank_memories(proxy, "Database SQLite", 5, None, False, [], [], False,
                             policy=RetrievalConfig(architecture="baseline"))
    assert baseline[0]["score_components"] == {"rrf": baseline[0]["score"]}


def test_claim_truth_confidence_is_separate_from_capture_confidence():
    memories = [
        Memory(id="high", content="Database uses PostgreSQL", confidence=0.2,
               claim_confidence=0.9),
        Memory(id="low", content="Database uses PostgreSQL", confidence=0.2,
               claim_confidence=0.1),
    ]
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: memories), vector_store=None,
        project_dir=".",
    )
    ranked = rank_memories(proxy, "Database uses PostgreSQL", 5, None, False, [], [], False,
                           policy=RetrievalConfig())
    scores = {row["memory"].id: row["score"] for row in ranked}
    assert scores["high"] > scores["low"]
    high = next(row for row in ranked if row["memory"].id == "high")
    assert high["score_components"]["claim_confidence"] == 0.9
    assert high["score_components"]["extraction_confidence"] == 0.2


def test_conflicting_requested_answer_slot_abstains_with_diagnostic():
    memories = [
        Memory(id="one", content="Database SQLite", answer_slots={"rationale": "simple"}),
        Memory(id="two", content="Database SQLite", answer_slots={"rationale": "scalable"}),
    ]
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: memories), vector_store=None
    )
    ranked = rank_memories(proxy, "Why SQLite?", 5, None, False, [], [], False,
                           policy=RetrievalConfig())
    assert not ranked
    assert ranked.status == "abstained_conflict"
    assert {row["reason"] for row in ranked.diagnostics} >= {"conflict_detected"}


def test_context_selector_avoids_near_duplicate_records():
    from oxmemory.storage.retrieval import build_context

    first = Memory(id="first", content="Database uses SQLite for local storage")
    duplicate = Memory(id="duplicate", content="Database uses SQLite for local storage")
    result = build_context([
        {"memory": first, "score": 0.9, "reasons": []},
        {"memory": duplicate, "score": 0.8, "reasons": []},
    ], 5000, query="Database storage")
    assert [row["memory"]["id"] for row in result["results"]] == ["first"]
    assert result["diagnostics"] == [{"memory_id": "duplicate", "reason": "duplicate_content"}]
    ranked_baseline = build_context([
        {"memory": first, "score": 0.9, "reasons": []},
        {"memory": duplicate, "score": 0.8, "reasons": []},
    ], 5000, query="Database storage", selection_strategy="ranked")
    assert len(ranked_baseline["results"]) == 2


def test_query_planner_extracts_intent_paths_symbols_and_history():
    from oxmemory.storage.query_planner import analyze_query

    plan = analyze_query("Where was create_user() defined in src/auth/service.py previously?")
    assert plan.intent == "historical_decision"
    assert plan.historical is True
    assert plan.symbols == ["create_user"]
    assert plan.file_paths == ["src/auth/service.py"]


def test_code_index_returns_separate_python_source_evidence(tmp_path):
    from oxmemory.storage.code_index import search_python_definitions

    source = tmp_path / "src" / "auth.py"
    source.parent.mkdir()
    source.write_text("def create_user(name):\n    return name\n", encoding="utf-8")
    assert not (tmp_path / "should_not_exist").exists()
    evidence = search_python_definitions(tmp_path, symbols=["create_user"], limit=2)
    assert evidence[0]["source_type"] == "repository_code"


def test_code_index_returns_multilanguage_definition_and_references(tmp_path):
    from oxmemory.storage.code_index import search_code_definitions

    (tmp_path / "auth.js").write_text("export async function authenticate_user(req) {\n  return req.user;\n}\n")
    (tmp_path / "routes.js").write_text("import { authenticate_user } from './auth';\n")
    evidence = search_code_definitions(tmp_path, symbols=["authenticate_user"], limit=5)
    definition = next(row for row in evidence if row["kind"] == "function")
    assert definition["language"] == "javascript"
    assert {ref["path"] for ref in definition["references"]} == {"routes.js"}
    assert evidence[0]["path"] == "auth.js"
    assert evidence[0]["start_line"] == 1


def test_recall_returns_code_evidence_within_context_budget(tmp_path):
    from oxmemory.core.config import get_default_config, save_config

    MarkdownManager(tmp_path).initialize_brain("Code recall")
    save_config(get_default_config("Code recall"), tmp_path)
    source = tmp_path / "service.py"
    source.write_text("def create_user(name):\n    return name\n", encoding="utf-8")
    with MemoryStore(tmp_path, enable_vectors=False) as store:
        result = store.recall_context("Where is create_user() defined?", token_budget=1000)
    assert result["status"] == "returned_code_evidence"
    assert result["code_evidence"][0]["symbol"] == "create_user"
    assert result["budget_used"] <= 1000


def test_structured_claim_conflicts_abstain_for_current_but_allow_history():
    memories = [
        Memory(id="sqlite", content="Production database uses SQLite", claim_subject="production database",
               claim_predicate="uses", claim_value="SQLite"),
        Memory(id="postgres", content="Production database uses PostgreSQL", claim_subject="production database",
               claim_predicate="uses", claim_value="PostgreSQL"),
    ]
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: memories), vector_store=None,
        project_dir=".",
    )
    current = rank_memories(proxy, "What production database is configured now?", 5,
                            None, False, [], [], False, policy=RetrievalConfig())
    assert current.status == "abstained_conflict"
    historical = rank_memories(proxy, "Which production database did we use previously?", 5,
                               None, False, [], [], False, policy=RetrievalConfig())
    assert historical.status == "answered_with_memory"
    assert {row["memory"].id for row in historical} == {"sqlite", "postgres"}


def test_conflicting_adoption_state_is_not_returned_as_approval():
    memories = [
        Memory(id="adopted", content="Production uses CockroachDB",
               claim_subject="production database", claim_predicate="uses",
               claim_value="CockroachDB", claim_environment="production", claim_state="adopted"),
        Memory(id="evaluating", content="Production is evaluating CockroachDB",
               claim_subject="production database", claim_predicate="uses",
               claim_value="CockroachDB", claim_environment="production", claim_state="evaluating"),
    ]
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: memories), vector_store=None,
        project_dir=".",
    )
    result = rank_memories(proxy, "Did we approve CockroachDB for production?", 5,
                           None, False, [], [], False, policy=RetrievalConfig())
    assert not result
    assert result.status == "abstained_conflict"


def test_explicit_claim_validity_bounds_filter_current_recall():
    from datetime import datetime, timedelta

    memory = Memory(content="Database uses SQLite", valid_to=datetime.now() - timedelta(days=1))
    proxy = SimpleNamespace(
        markdown=SimpleNamespace(get_all_memories=lambda: [memory]), vector_store=None,
        project_dir=".",
    )
    result = rank_memories(proxy, "What database is currently configured?", 5,
                           None, False, [], [], False, policy=RetrievalConfig())
    assert not result
    assert result.diagnostics[0]["reason"] == "temporal_out_of_range"


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


def test_edam_defaults_and_baseline_mode_are_configurable(tmp_path):
    from oxmemory.core.config import get_default_config, load_config, save_config
    from oxmemory.core.models import RetrievalConfig

    MarkdownManager(tmp_path).initialize_brain("Configuration")
    save_config(get_default_config("Configuration"), tmp_path)
    config = load_config(tmp_path)
    assert config.retrieval.architecture == "edam"
    assert config.retrieval.relevance_gate
    config.retrieval = RetrievalConfig(architecture="edam", relevance_gate=True,
                                       min_similarity=0.7)
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
    assert len(dev) == 9 and len(test) == 17
    assert sum(bool(c["relevant"]) for c in dev) == 4
    assert sum(bool(c["relevant"]) for c in test) == 9
    assert not {c["id"] for c in dev} & {c["id"] for c in test}
