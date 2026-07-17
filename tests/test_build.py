from pathlib import Path

from generator.build import build
from generator.parser import FTBQuestParser
from generator.validator import ProjectValidator


def test_build_generates_playable_core_chapters(tmp_path: Path) -> None:
    quests_root = build(tmp_path / "config" / "ftbquests")
    project = FTBQuestParser().load(quests_root)
    report = ProjectValidator().validate(project)

    assert (quests_root / "chapters" / "00_welcome.snbt").is_file()
    assert (quests_root / "chapters" / "01_survival.snbt").is_file()
    assert (quests_root / "chapters" / "02_mining.snbt").is_file()
    assert (quests_root / "chapters" / "03_exploration.snbt").is_file()
    assert (quests_root / "chapters" / "04_create.snbt").is_file()
    assert (quests_root / "chapters" / "05_actually_additions.snbt").is_file()
    assert (quests_root / "chapters" / "06_ars_nouveau.snbt").is_file()
    assert (quests_root / "chapters" / "07_apotheosis.snbt").is_file()
    assert (quests_root / "chapters" / "08_ae2.snbt").is_file()
    assert (quests_root / "chapters" / "09_mekanism.snbt").is_file()
    assert (quests_root / "chapters" / "10_endgame.snbt").is_file()
    assert (quests_root / "chapters" / "11_challenges.snbt").is_file()
    assert (quests_root / "chapters" / "12_create_addons.snbt").is_file()
    assert len(project.chapters) == 13
    assert len(project.quests) == 516
    assert report.is_valid
