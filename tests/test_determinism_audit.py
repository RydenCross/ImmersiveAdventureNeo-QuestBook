from __future__ import annotations

import json

from generator.cli import main
from generator.determinism_audit import compare_generated_trees, run_determinism_audit


def test_checked_in_builder_is_deterministic() -> None:
    result = run_determinism_audit()
    assert result.is_clean
    assert result.file_count == 18
    assert result.total_bytes > 0
    assert len(result.tree_digest) == 64


def test_comparison_detects_changed_file(tmp_path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "data.snbt").write_text("one\n", encoding="utf-8")
    (second / "data.snbt").write_text("two\n", encoding="utf-8")
    result = compare_generated_trees(first, second)
    assert not result.is_clean
    assert result.changed_files == ("data.snbt",)


def test_comparison_detects_missing_and_added_files(tmp_path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "old.snbt").write_text("old\n", encoding="utf-8")
    (second / "new.snbt").write_text("new\n", encoding="utf-8")
    result = compare_generated_trees(first, second)
    assert result.missing_from_second == ("old.snbt",)
    assert result.added_in_second == ("new.snbt",)


def test_cli_writes_determinism_report(tmp_path) -> None:
    output = tmp_path / "determinism-audit.json"
    assert main(["determinism-audit", "--strict", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["file_count"] == 18


def test_tree_digest_is_stable_between_runs() -> None:
    first = run_determinism_audit()
    second = run_determinism_audit()
    assert first.tree_digest == second.tree_digest
