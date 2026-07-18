from pathlib import Path

from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.progression_planner import generate_quest_blueprint


def test_generates_dependency_safe_chapter_blueprint(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    result = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    assert result.is_clean
    assert result.quest_count == 4
    assert len(result.chapters) == 1
    quests = {quest.objective.identifier: quest for quest in result.chapters[0].quests}
    assert quests["scanner_demo:copper_gear"].quest_id in quests[
        "scanner_demo:assembly_machine"
    ].prerequisite_quests


def test_blueprint_is_deterministic_and_has_unique_layout(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    first = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    second = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    assert first.format_json() == second.format_json()
    positions = [(quest.x, quest.y) for chapter in first.chapters for quest in chapter.quests]
    assert len(positions) == len(set(positions))


def test_blueprint_reports_candidate_shortfall(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    result = generate_quest_blueprint(pack, target_quests=20, chapter_size=10)
    assert result.is_clean
    assert result.shortfall > 0
    assert any("progression-safe candidates" in warning for warning in result.warnings)


def test_invalid_blueprint_limits_fail(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)

    result = generate_quest_blueprint(pack, target_quests=0, chapter_size=2)
    assert not result.is_clean
    assert any("target quests" in error for error in result.errors)
    assert any("chapter size" in error for error in result.errors)
