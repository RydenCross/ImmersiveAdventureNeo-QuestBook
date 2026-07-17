from __future__ import annotations

import json

from content import create_project
from generator.chapter_audit import audit_chapters, run_chapter_audit
from generator.cli import main


def test_checked_in_chapters_pass_integrity_audit() -> None:
    result = run_chapter_audit()
    assert result.is_clean
    assert result.chapter_count == 13
    assert result.quest_count == 656
    assert sum(result.chapter_sizes.values()) == 656


def test_audit_detects_duplicate_chapter_uuid_and_ftb_id() -> None:
    project = create_project()
    project.chapters[1].uuid = project.chapters[0].uuid
    project.chapters[1].ftb_id = project.chapters[0].ftb_id
    result = audit_chapters(project)
    assert not result.is_clean
    assert len(result.duplicate_uuids) == 1
    assert len(result.duplicate_ftb_ids) == 1


def test_audit_detects_invalid_metadata_and_empty_chapter() -> None:
    project = create_project()
    chapter = project.chapters[0]
    chapter.icon = "Bad Icon"
    chapter.description = ""
    chapter.quests.clear()
    result = audit_chapters(project)
    assert not result.is_clean
    assert chapter.id in result.empty_chapters
    assert any("invalid icon" in issue for issue in result.invalid_chapters)
    assert any("description is empty" in issue for issue in result.invalid_chapters)


def test_audit_detects_order_mismatch() -> None:
    project = create_project()
    project.chapters[0].raw_data["order_index"] = 1
    result = audit_chapters(project)
    assert not result.is_clean
    assert result.order_issues


def test_cli_writes_chapter_audit_report(tmp_path) -> None:
    output = tmp_path / "chapter-audit.json"
    assert main(["chapter-audit", "--strict", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["chapter_count"] == 13
    assert payload["quest_count"] == 656
