from __future__ import annotations

import json

from content import create_project
from generator.cli import main
from generator.contract_guard import (
    ContractManifest,
    build_contract_manifest,
    compare_contract_manifests,
    run_contract_guard,
)


def test_checked_in_contract_baseline_passes() -> None:
    result = run_contract_guard()
    assert result.is_clean
    assert result.current.quest_count == 656
    assert result.current.task_count > 0
    assert result.current.reward_count > 0


def test_guard_detects_removed_and_changed_contracts() -> None:
    baseline = build_contract_manifest(create_project())
    changed = dict(baseline.quests[0])
    changed["icon"] = "minecraft:barrier"
    current = ContractManifest((changed,) + baseline.quests[2:])
    result = compare_contract_manifests(baseline, current)
    assert not result.is_clean
    assert len(result.missing_quests) == 1
    assert len(result.changed_quests) == 1


def test_description_changes_are_not_part_of_contract() -> None:
    project = create_project()
    baseline = build_contract_manifest(project)
    project.chapters[0].quests[0].description = "Edited prose is safe."
    assert compare_contract_manifests(baseline, build_contract_manifest(project)).is_clean


def test_cli_writes_contract_guard_report(tmp_path) -> None:
    output = tmp_path / "contract-guard.json"
    assert main(["contract-guard", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["current"]["quests"] == 656


def test_cli_refreshes_contract_baseline(tmp_path) -> None:
    output = tmp_path / "contract-baseline.json"
    assert main(["contract-baseline", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["quest_count"] == 656
