"""Labels, metrics, and real Git behavior for the controlled ablation."""

import hashlib
from collections import Counter
from unittest.mock import Mock

import pytest

from oxmemory.benchmark import collect, measure, run
from oxmemory.benchmark_data import scenarios
from oxmemory.storage.markdown import MarkdownManager
from oxmemory.storage.memory_store import MemoryStore


def test_dataset_is_partitioned_before_execution():
    cases = scenarios()["scenarios"]
    assert len(cases) == len({c["id"] for c in cases}) == 34
    assert Counter(c["category"] for c in cases) == {
        "changed": 8,
        "unrelated": 6,
        "valid": 6,
        "superseded": 6,
        "no_answer": 4,
        "evidence_missing": 2,
        "ambiguous": 2,
    }
    development = [c for c in cases if c["partition"] == "development"]
    assert len(development) == 7
    assert len({c["category"] for c in development}) == 7


def test_metrics_distinguish_unknown_truth_from_pending_verification():
    result = measure(["noise", "true-but-stale"], {"true-but-stale"}, set(), {"true-but-stale"})
    assert result["recall_at_k"] == 1
    assert result["reciprocal_rank"] == 0.5
    assert result["outdated_hit"] is None
    assert result["ineligible_hit"] is True
    assert result["no_answer_false_positive"] is None
    missing = measure(["noise"], set(), {"old"}, {"old"})
    assert missing["recall_at_k"] is None
    assert missing["no_answer_false_positive"] is True
    assert measure([], set(), set(), set())["no_answer_false_positive"] is False
    assert measure(["new", "old"], {"new"}, {"old"}, {"old"}, "new")["update_correct"] is False


def test_real_git_development_workflow_and_artifacts(tmp_path):
    output = tmp_path / "report"
    report = run(output, partition="development")
    assert hashlib.sha256((output / "scenarios.json").read_bytes()).hexdigest() == report[
        "dataset_sha256"
    ]
    for name, expected in report["environment"]["source_sha256"].items():
        assert hashlib.sha256((output / "source" / name).read_bytes()).hexdigest() == expected
    assert len(report["audits"]) == 7
    rows = {(r["category"], r["checkpoint"], r["variant"]): r for r in report["results"]}
    assert rows["changed", "after_observation", "basic"]["metrics"]["outdated_hit"] is True
    # Both baseline lifecycle policies preserve review-required memories when
    # file changes only establish uncertainty; only contradiction can prove false.
    assert rows["changed", "after_observation", "current"]["metrics"]["outdated_hit"] is True
    assert rows["valid", "pending_review", "current"]["metrics"]["recall_at_k"] == 1
    assert rows["valid", "after_review", "current"]["metrics"]["recall_at_k"] == 1
    assert rows["superseded", "after_review", "current"]["metrics"]["update_correct"] is True
    assert (
        rows["unrelated", "after_observation", "basic"]["retrieved"]
        == rows["unrelated", "after_observation", "current"]["retrieved"]
    )
    assert (
        rows["no_answer", "after_observation", "basic"]["retrieved"]
        == rows["no_answer", "after_observation", "current"]["retrieved"]
    )
    for audit in report["audits"]:
        assert len(audit["initial_commit"]) == len(audit["changed_commit"]) == 40
        assert audit["initial_commit"] != audit["changed_commit"]
        assert audit["diff"]
    for name in [
        "REPORT.md",
        "results.json",
        "summary.csv",
        "scenarios.json",
        "charts/development.svg",
    ]:
        assert (output / name).is_file()
    with pytest.raises(FileExistsError):
        run(output, partition="development")


def test_semantic_failure_never_becomes_keyword_success(tmp_path):
    MarkdownManager(tmp_path).initialize_brain("Failure test")
    with MemoryStore(tmp_path, enable_vectors=False) as store:
        memory = store.add("Tasks persist in JSON files.")
        vector = Mock()
        vector.count.return_value = 1
        vector.search.side_effect = RuntimeError("Embedding backend unavailable")
        with pytest.raises(RuntimeError, match="Embedding backend unavailable"):
            collect(store, scenarios()["scenarios"][0], {"original": memory.id}, "test", vector, 5)
