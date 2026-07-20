from __future__ import annotations

import json

from content import create_project
from generator.cli import main
from generator.text_audit import audit_text, run_text_audit


def test_checked_in_text_passes_quality_audit() -> None:
    result = run_text_audit()
    assert result.is_clean
    assert result.chapter_count == 13
    assert result.quest_count == 656


def test_audit_detects_placeholder_text() -> None:
    project = create_project()
    project.quests[0].description = "TODO: write this later"
    result = audit_text(project)
    assert not result.is_clean
    assert result.placeholder_text


def test_audit_detects_malformed_text() -> None:
    project = create_project()
    project.quests[0].description = "Bad  spacing"
    result = audit_text(project)
    assert not result.is_clean
    assert result.malformed_text


def test_audit_detects_duplicate_substantive_descriptions() -> None:
    project = create_project()
    text = "This deliberately duplicated description is long enough to be meaningful."
    project.quests[0].description = text
    project.quests[1].description = text
    result = audit_text(project)
    assert not result.is_clean
    assert result.duplicate_descriptions


def test_cli_writes_text_audit_report(tmp_path) -> None:
    output = tmp_path / "text-audit.json"
    assert main(["text-audit", "--strict", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["quest_count"] == 656
