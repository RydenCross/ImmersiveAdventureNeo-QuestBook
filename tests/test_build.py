from pathlib import Path

from generator.build import build
from generator.parser import FTBQuestParser
from generator.validator import ProjectValidator


def test_build_generates_playable_welcome_and_survival_chapters(tmp_path: Path) -> None:
    quests_root = build(tmp_path / "config" / "ftbquests")
    project = FTBQuestParser().load(quests_root)
    report = ProjectValidator().validate(project)

    assert (quests_root / "chapters" / "00_welcome.snbt").is_file()
    assert (quests_root / "chapters" / "01_survival.snbt").is_file()
    assert len(project.chapters) == 2
    assert len(project.quests) == 34
    assert report.is_valid
