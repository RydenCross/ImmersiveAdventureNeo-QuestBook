from __future__ import annotations

import json

from content import create_project
from generator.cli import main
from generator.identity_guard import (
    IdentityManifest,
    build_identity_manifest,
    compare_identity_manifests,
    run_identity_guard,
)


def test_checked_in_identity_baseline_passes() -> None:
    result = run_identity_guard()
    assert result.is_clean
    assert result.current.quest_count == 656
    assert result.current.chapter_count == 13


def test_guard_detects_removed_and_changed_identities() -> None:
    baseline = build_identity_manifest(create_project())
    changed_quest = dict(baseline.quests[0])
    changed_quest["title"] = "Renamed without baseline refresh"
    current = IdentityManifest(
        chapters=baseline.chapters[1:],
        quests=(changed_quest,) + baseline.quests[2:],
    )
    result = compare_identity_manifests(baseline, current)
    assert not result.is_clean
    assert len(result.missing_chapters) == 1
    assert len(result.missing_quests) == 1
    assert len(result.changed_quests) == 1


def test_cli_writes_identity_guard_report(tmp_path) -> None:
    output = tmp_path / "identity-guard.json"
    assert main(["identity-guard", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["current"]["quests"] == 656


def test_cli_refreshes_identity_baseline(tmp_path) -> None:
    output = tmp_path / "identity-baseline.json"
    assert main(["identity-baseline", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["quest_count"] == 656
    assert payload["chapter_count"] == 13
