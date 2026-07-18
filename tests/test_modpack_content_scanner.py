from __future__ import annotations

from pathlib import Path

from generator.modpack_content_scanner import scan_modpack_content
from generator.modpack_content_scanner_contract import _synthetic_pack


def test_scans_recipes_advancements_registries_and_tags(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    result = scan_modpack_content(pack, candidate_limit=20)
    assert result.is_clean
    assert len(result.recipes) == 2
    assert len(result.advancements) == 2
    assert len(result.registries) >= 2
    assert len(result.tags) == 1
    assert result.pack_name == "Scanner Contract Pack"


def test_recipe_outputs_form_candidate_dependencies(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    result = scan_modpack_content(pack, candidate_limit=20)
    candidates = {candidate.objective_id: candidate for candidate in result.candidates}
    gear = candidates["scanner_demo:copper_gear"]
    machine = candidates["scanner_demo:assembly_machine"]
    assert gear.candidate_id in machine.prerequisite_candidates
    assert "c:ingots/iron" in machine.prerequisite_tags
    assert result.graph_edges >= 2


def test_candidate_limit_is_enforced_and_invalid_limits_fail(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    limited = scan_modpack_content(pack, candidate_limit=3)
    assert limited.is_clean
    assert len(limited.candidates) == 3

    invalid = scan_modpack_content(pack, candidate_limit=0)
    assert not invalid.is_clean
    assert "candidate limit" in invalid.errors[0]


def test_broken_content_json_becomes_warning_not_crash(tmp_path: Path) -> None:
    pack = tmp_path / "broken.mrpack"
    _synthetic_pack(pack, include_broken_json=True)

    result = scan_modpack_content(pack, candidate_limit=20)
    assert result.is_clean
    assert any("broken.json" in warning for warning in result.warnings)
