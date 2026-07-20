from dataclasses import replace
from pathlib import Path

from generator.ftb_blueprint_exporter import export_quest_blueprint
from generator.modpack_content_scanner_contract import _synthetic_pack
from generator.parser import FTBQuestParser
from generator.progression_planner import generate_quest_blueprint
from model import TaskType


def test_exports_blueprint_to_installable_ftb_quests_tree(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    result = export_quest_blueprint(blueprint, tmp_path / "config" / "ftbquests")

    assert result.is_clean
    assert result.chapters == 1
    assert result.quests == 4
    assert "quests/data.snbt" in result.files
    restored = FTBQuestParser().load(tmp_path / "config" / "ftbquests")
    assert {task.type for quest in restored.quests for task in quest.tasks} == {
        TaskType.ITEM,
        TaskType.ADVANCEMENT,
    }
    assert sum(len(quest.dependencies) for quest in restored.quests) == 2


def test_export_is_deterministic_and_removes_stale_chapters(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)
    destination = tmp_path / "ftbquests"

    first = export_quest_blueprint(blueprint, destination)
    stale = destination / "quests" / "chapters" / "stale.snbt"
    stale.write_text('{ id: "0000000000000000" }\n', encoding="utf-8")
    second = export_quest_blueprint(blueprint, destination)

    assert first.tree_sha256 == second.tree_sha256
    assert not stale.exists()


def test_export_rejects_blueprints_with_errors(tmp_path: Path) -> None:
    pack = tmp_path / "example.mrpack"
    _synthetic_pack(pack)
    blueprint = generate_quest_blueprint(pack, target_quests=4, chapter_size=10)

    result = export_quest_blueprint(
        replace(blueprint, errors=("synthetic error",)),
        tmp_path / "ftbquests",
    )

    assert not result.is_clean
    assert any("cannot export" in error for error in result.errors)
