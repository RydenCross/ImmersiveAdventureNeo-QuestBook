from pathlib import Path

from generator.build import build
from generator.parser import FTBQuestParser


def test_build_generates_playable_welcome_chapter(tmp_path: Path) -> None:
    quests_root = build(tmp_path / "config" / "ftbquests")
    project = FTBQuestParser().load(quests_root)

    assert (quests_root / "chapters" / "00_welcome.snbt").is_file()
    assert len(project.chapters) == 1
    assert len(project.quests) == 9
